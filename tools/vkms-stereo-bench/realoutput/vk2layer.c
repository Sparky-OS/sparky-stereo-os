// SPDX-License-Identifier: MIT
/*
 * vk2layer: the smallest real stereo Vulkan client on Wayland. One xdg toplevel whose swapchain has two array
 * layers (the left eye in layer 0, the right eye in layer 1), which the edition's Mesa packs side by side and
 * declares to the compositor. Every frame clears layer 0 to red and layer 1 to green, with a blue level that
 * counts the frames, so each presented picture is new and its two halves must differ.
 *
 *   SWAPCHAINS  how many swapchains are made one after the other, each replacing the last (default 3)
 *   FRAMES      frames presented on each swapchain (default 3)
 *   HOLD        seconds to stay after the last frame (default 10)
 *   SAME=1      both layers red: the control whose halves must match
 */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define VK_USE_PLATFORM_WAYLAND_KHR
#include <vulkan/vulkan.h>
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"

static struct wl_compositor *compositor;
static struct xdg_wm_base *wm_base;
static bool configured;

static void check(VkResult result, const char *what)
{
	if (result != VK_SUCCESS) {
		fprintf(stderr, "vk2layer: %s: Vulkan error %d\n", what, result);
		exit(1);
	}
}

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
	if (!strcmp(interface, wl_compositor_interface.name))
		compositor = wl_registry_bind(registry, name, &wl_compositor_interface, 4);
	else if (!strcmp(interface, xdg_wm_base_interface.name))
		wm_base = wl_registry_bind(registry, name, &xdg_wm_base_interface, 1);
}
static void global_remove(void *data, struct wl_registry *registry, uint32_t name) {}
static const struct wl_registry_listener registry_listener = { global, global_remove };
static void ping(void *data, struct xdg_wm_base *base, uint32_t serial) { xdg_wm_base_pong(base, serial); }
static const struct xdg_wm_base_listener wm_listener = { ping };
static void surface_configure(void *data, struct xdg_surface *surface, uint32_t serial)
{
	xdg_surface_ack_configure(surface, serial);
	configured = true;
}
static const struct xdg_surface_listener surface_listener = { surface_configure };
static void toplevel_configure(void *data, struct xdg_toplevel *t, int32_t w, int32_t h, struct wl_array *s) {}
static void toplevel_close(void *data, struct xdg_toplevel *t) { exit(0); }
static const struct xdg_toplevel_listener toplevel_listener = { toplevel_configure, toplevel_close };

static int number(const char *name, int fallback)
{
	const char *value = getenv(name);
	return value ? atoi(value) : fallback;
}

int main(void)
{
	const int swapchains = number("SWAPCHAINS", 3), frames = number("FRAMES", 3);
	const bool same = getenv("SAME") != NULL;
	struct wl_display *display = wl_display_connect(NULL);
	assert(display);
	struct wl_registry *registry = wl_display_get_registry(display);
	wl_registry_add_listener(registry, &registry_listener, NULL);
	wl_display_roundtrip(display);
	assert(compositor && wm_base);
	xdg_wm_base_add_listener(wm_base, &wm_listener, NULL);
	struct wl_surface *wl_surface = wl_compositor_create_surface(compositor);
	struct xdg_surface *xdg_surface = xdg_wm_base_get_xdg_surface(wm_base, wl_surface);
	struct xdg_toplevel *toplevel = xdg_surface_get_toplevel(xdg_surface);
	xdg_surface_add_listener(xdg_surface, &surface_listener, NULL);
	xdg_toplevel_add_listener(toplevel, &toplevel_listener, NULL);
	xdg_toplevel_set_title(toplevel, "vk2layer");
	wl_surface_commit(wl_surface);
	while (!configured)
		wl_display_roundtrip(display);

	const char *instance_extensions[] = { VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_WAYLAND_SURFACE_EXTENSION_NAME };
	VkApplicationInfo app = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .pApplicationName = "vk2layer", .apiVersion = VK_API_VERSION_1_1 };
	VkInstanceCreateInfo instance_info = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &app,
		.enabledExtensionCount = 2, .ppEnabledExtensionNames = instance_extensions };
	VkInstance instance;
	check(vkCreateInstance(&instance_info, NULL, &instance), "instance");
	VkWaylandSurfaceCreateInfoKHR surface_info = { .sType = VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR, .display = display, .surface = wl_surface };
	VkSurfaceKHR surface;
	check(vkCreateWaylandSurfaceKHR(instance, &surface_info, NULL, &surface), "surface");
	uint32_t count = 1;
	VkPhysicalDevice physical;
	VkResult r = vkEnumeratePhysicalDevices(instance, &count, &physical);
	assert((r == VK_SUCCESS || r == VK_INCOMPLETE) && count == 1);
	VkPhysicalDeviceProperties props;
	vkGetPhysicalDeviceProperties(physical, &props);
	VkSurfaceCapabilitiesKHR caps;
	check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps), "capabilities");
	printf("device %s, maxImageArrayLayers %u\n", props.deviceName, caps.maxImageArrayLayers);
	if (caps.maxImageArrayLayers < 2) {
		fprintf(stderr, "vk2layer: the surface offers no second layer\n");
		return 2;
	}
	float priority = 1;
	VkDeviceQueueCreateInfo queue_info = { .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, .queueCount = 1, .pQueuePriorities = &priority };
	const char *device_extensions[] = { VK_KHR_SWAPCHAIN_EXTENSION_NAME };
	VkDeviceCreateInfo device_info = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, .queueCreateInfoCount = 1, .pQueueCreateInfos = &queue_info,
		.enabledExtensionCount = 1, .ppEnabledExtensionNames = device_extensions };
	VkDevice device;
	check(vkCreateDevice(physical, &device_info, NULL, &device), "device");
	VkQueue queue;
	vkGetDeviceQueue(device, 0, 0, &queue);
	VkCommandPoolCreateInfo pool_info = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT };
	VkCommandPool pool;
	check(vkCreateCommandPool(device, &pool_info, NULL, &pool), "pool");
	VkCommandBufferAllocateInfo alloc = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .commandPool = pool, .commandBufferCount = 1 };
	VkCommandBuffer command;
	check(vkAllocateCommandBuffers(device, &alloc, &command), "command buffer");
	VkFenceCreateInfo fence_info = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
	VkFence fence;
	check(vkCreateFence(device, &fence_info, NULL, &fence), "fence");

	VkSwapchainKHR swapchain = VK_NULL_HANDLE;
	int n = 0;
	for (int s = 0; s < swapchains; s++) {
		VkSwapchainCreateInfoKHR info = { .sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR, .surface = surface, .minImageCount = caps.minImageCount < 2 ? 2 : caps.minImageCount,
			.imageFormat = VK_FORMAT_B8G8R8A8_UNORM, .imageColorSpace = VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
			.imageExtent = { 640 + 32 * s, 360 }, .imageArrayLayers = 2, .imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT,
			.preTransform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR, .compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
			.presentMode = VK_PRESENT_MODE_FIFO_KHR, .clipped = VK_TRUE, .oldSwapchain = swapchain };
		VkSwapchainKHR next;
		check(vkCreateSwapchainKHR(device, &info, NULL, &next), "swapchain");
		if (swapchain)
			vkDestroySwapchainKHR(device, swapchain, NULL);
		swapchain = next;
		uint32_t image_count = 8;
		VkImage images[8];
		r = vkGetSwapchainImagesKHR(device, swapchain, &image_count, images);
		assert(r == VK_SUCCESS || r == VK_INCOMPLETE);
		for (int f = 0; f < frames; f++, n++) {
			uint32_t index;
			check(vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, VK_NULL_HANDLE, fence, &index), "acquire");
			check(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX), "acquire wait");
			vkResetFences(device, 1, &fence);
			VkCommandBufferBeginInfo begin = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO };
			check(vkBeginCommandBuffer(command, &begin), "begin");
			VkImageMemoryBarrier barrier = { .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
				.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
				.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .image = images[index],
				.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 2 } };
			vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0, NULL, 1, &barrier);
			const float blue = (n % 8) / 8.0f;
			VkClearColorValue colors[2] = { { { 1, 0, blue, 1 } }, { { same ? 1 : 0, same ? 0 : 1, blue, 1 } } };
			for (uint32_t layer = 0; layer < 2; layer++)
				vkCmdClearColorImage(command, images[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &colors[layer], 1,
						     &(VkImageSubresourceRange){ VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, layer, 1 });
			barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
			barrier.dstAccessMask = 0;
			barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
			barrier.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
			vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, NULL, 0, NULL, 1, &barrier);
			check(vkEndCommandBuffer(command), "end");
			VkSubmitInfo submit = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1, .pCommandBuffers = &command };
			check(vkQueueSubmit(queue, 1, &submit, fence), "submit");
			check(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX), "submit wait");
			vkResetFences(device, 1, &fence);
			VkPresentInfoKHR present = { .sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR, .swapchainCount = 1, .pSwapchains = &swapchain, .pImageIndices = &index };
			check(vkQueuePresentKHR(queue, &present), "present");
			wl_display_roundtrip(display);
			printf("swapchain %d frame %d presented (image %u, %dx360)\n", s, f, index, 640 + 32 * s);
			fflush(stdout);
			usleep(300000);
		}
	}
	for (int i = number("HOLD", 10) * 10; i > 0; i--) {
		wl_display_roundtrip(display);
		usleep(100000);
	}
	return 0;
}
