/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define VK_USE_PLATFORM_XCB_KHR
#include <vulkan/vulkan.h>
#include <xcb/xcb.h>

static void
check_result(VkResult result, int line)
{
   if (result != VK_SUCCESS) {
      fprintf(stderr, "Vulkan error %d at line %d\n", result, line);
      abort();
   }
}

#define check(result) check_result((result), __LINE__)

static bool
has_extension(const char *name, uint32_t count, VkExtensionProperties *props)
{
   for (uint32_t i = 0; i < count; i++)
      if (!strcmp(name, props[i].extensionName))
         return true;
   return false;
}

static xcb_atom_t
atom(xcb_connection_t *conn, const char *name)
{
   xcb_intern_atom_reply_t *reply = xcb_intern_atom_reply(
      conn, xcb_intern_atom(conn, 0, strlen(name), name), NULL);
   assert(reply);
   xcb_atom_t result = reply->atom;
   free(reply);
   return result;
}

static void
set_stereo_support(xcb_connection_t *conn, xcb_window_t root, uint32_t version)
{
   xcb_atom_t property = atom(conn, "_KDE_NET_WM_STEREO_CONTENT_SUPPORTED");
   xcb_change_property(conn, XCB_PROP_MODE_REPLACE, root, property,
                       XCB_ATOM_CARDINAL, 32, 1, &version);
   xcb_flush(conn);
}

static uint32_t
stereo_declaration(xcb_connection_t *conn, xcb_window_t window)
{
   xcb_atom_t property = atom(conn, "_KDE_NET_WM_STEREO_CONTENT");
   xcb_get_property_reply_t *reply = xcb_get_property_reply(
      conn, xcb_get_property(conn, 0, window, property, XCB_ATOM_CARDINAL,
                             0, 1), NULL);
   assert(reply && reply->format == 32 &&
          xcb_get_property_value_length(reply) >= (int)sizeof(uint32_t));
   uint32_t value = *(const uint32_t *)xcb_get_property_value(reply);
   free(reply);
   return value;
}

int
main(void)
{
   const char *mode = getenv("X11VK_MODE") ? getenv("X11VK_MODE") : "plain";
   uint32_t cx = 100, cy = 80, width = 200, height = 150;
   if (!strcmp(mode, "overflow")) { cx = 250; cy = 200; width = 300; height = 200; }
   xcb_connection_t *conn = xcb_connect(NULL, NULL);
   assert(conn && !xcb_connection_has_error(conn));
   const xcb_setup_t *setup = xcb_get_setup(conn);
   xcb_screen_iterator_t screen_iter = xcb_setup_roots_iterator(setup);
   xcb_screen_t *screen = screen_iter.data;

   xcb_window_t parent = xcb_generate_id(conn);
   uint32_t pvalues[] = {0x808080, XCB_EVENT_MASK_EXPOSURE};
   xcb_create_window(conn, XCB_COPY_FROM_PARENT, parent, screen->root, 200, 150, 400, 300, 0,
                     XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, pvalues);
   xcb_window_t window = xcb_generate_id(conn);
   uint32_t values[] = {screen->black_pixel, XCB_EVENT_MASK_EXPOSURE};
   xcb_create_window(conn, XCB_COPY_FROM_PARENT, window, parent, cx, cy, width, height, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT,
                     screen->root_visual, XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, values);
   xcb_map_window(conn, window);
   xcb_map_window(conn, parent);
   xcb_flush(conn);
   printf("parent=0x%x child=0x%x sibling=0x0 place=%u,%u,%u,%u sib=0,0,0,0 stereo=1\n", parent, window, cx, cy, width, height);
   fflush(stdout);

   uint32_t instance_count = 0;
   check(vkEnumerateInstanceExtensionProperties(NULL, &instance_count, NULL));
   VkExtensionProperties *instance_ext = calloc(instance_count, sizeof(*instance_ext));
   check(vkEnumerateInstanceExtensionProperties(NULL, &instance_count, instance_ext));
   assert(has_extension(VK_KHR_SURFACE_EXTENSION_NAME, instance_count, instance_ext));
   assert(has_extension(VK_KHR_XCB_SURFACE_EXTENSION_NAME, instance_count, instance_ext));
   free(instance_ext);

   const char *instance_extensions[] = {
      VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_XCB_SURFACE_EXTENSION_NAME,
   };
   VkApplicationInfo app = {
      .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
      .pApplicationName = "mesa-vulkan-stereo",
      .apiVersion = VK_API_VERSION_1_1,
   };
   VkInstanceCreateInfo instance_info = {
      .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
      .pApplicationInfo = &app,
      .enabledExtensionCount = 2,
      .ppEnabledExtensionNames = instance_extensions,
   };
   VkInstance instance;
   check(vkCreateInstance(&instance_info, NULL, &instance));

   VkSurfaceKHR surface;
   VkXcbSurfaceCreateInfoKHR surface_info = {
      .sType = VK_STRUCTURE_TYPE_XCB_SURFACE_CREATE_INFO_KHR,
      .connection = conn,
      .window = window,
   };
   check(vkCreateXcbSurfaceKHR(instance, &surface_info, NULL, &surface));

   uint32_t physical_count = 0;
   check(vkEnumeratePhysicalDevices(instance, &physical_count, NULL));
   assert(physical_count > 0);
   VkPhysicalDevice *physical_devices = calloc(physical_count, sizeof(*physical_devices));
   check(vkEnumeratePhysicalDevices(instance, &physical_count, physical_devices));
   VkPhysicalDevice physical = physical_devices[0];
   free(physical_devices);

   VkSurfaceCapabilitiesKHR caps;
   check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   assert(caps.maxImageArrayLayers == 2);

   uint32_t queue_count = 0;
   vkGetPhysicalDeviceQueueFamilyProperties(physical, &queue_count, NULL);
   VkQueueFamilyProperties *queue_props = calloc(queue_count, sizeof(*queue_props));
   vkGetPhysicalDeviceQueueFamilyProperties(physical, &queue_count, queue_props);
   uint32_t queue_family = UINT32_MAX;
   for (uint32_t i = 0; i < queue_count; i++) {
      VkBool32 present = VK_FALSE;
      check(vkGetPhysicalDeviceSurfaceSupportKHR(physical, i, surface, &present));
      if (present && (queue_props[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
         queue_family = i;
         break;
      }
   }
   assert(queue_family != UINT32_MAX);
   free(queue_props);

   float priority = 1.0f;
   VkDeviceQueueCreateInfo queue_info = {
      .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
      .queueFamilyIndex = queue_family,
      .queueCount = 1,
      .pQueuePriorities = &priority,
   };
   const char *device_extensions[] = {VK_KHR_SWAPCHAIN_EXTENSION_NAME};
   VkDeviceCreateInfo device_info = {
      .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
      .queueCreateInfoCount = 1,
      .pQueueCreateInfos = &queue_info,
      .enabledExtensionCount = 1,
      .ppEnabledExtensionNames = device_extensions,
   };
   VkDevice device;
   check(vkCreateDevice(physical, &device_info, NULL, &device));
   VkQueue queue;
   vkGetDeviceQueue(device, queue_family, 0, &queue);

   VkSwapchainCreateInfoKHR swapchain_info = {
      .sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
      .surface = surface,
      .minImageCount = 2,
      .imageFormat = VK_FORMAT_B8G8R8A8_UNORM,
      .imageColorSpace = VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
      .imageExtent = {width, height},
      .imageArrayLayers = 2,
      .imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT,
      .imageSharingMode = VK_SHARING_MODE_EXCLUSIVE,
      .preTransform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR,
      .compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
      .presentMode = VK_PRESENT_MODE_FIFO_KHR,
      .clipped = VK_TRUE,
   };
   VkSwapchainKHR swapchain;
   check(vkCreateSwapchainKHR(device, &swapchain_info, NULL, &swapchain));
   fprintf(stderr, "declaration=%d\n", (int)stereo_declaration(conn, window));

   uint32_t image_count = 0;
   check(vkGetSwapchainImagesKHR(device, swapchain, &image_count, NULL));
   assert(image_count >= 2);
   VkImage *images = calloc(image_count, sizeof(*images));
   check(vkGetSwapchainImagesKHR(device, swapchain, &image_count, images));

   VkCommandPoolCreateInfo pool_info = {
      .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
      .queueFamilyIndex = queue_family,
   };
   VkCommandPool pool;
   check(vkCreateCommandPool(device, &pool_info, NULL, &pool));
   VkCommandBufferAllocateInfo alloc_info = {
      .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
      .commandPool = pool,
      .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
      .commandBufferCount = 1,
   };
   VkCommandBuffer command;
   check(vkAllocateCommandBuffers(device, &alloc_info, &command));
   VkSemaphoreCreateInfo semaphore_info = {
      .sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
   };
   VkSemaphore acquire, present;
   check(vkCreateSemaphore(device, &semaphore_info, NULL, &acquire));
   check(vkCreateSemaphore(device, &semaphore_info, NULL, &present));
   for (;;) {
   uint32_t image_index;
   VkResult acquire_result = vkAcquireNextImageKHR(device, swapchain,
                                                   UINT64_MAX, acquire,
                                                   VK_NULL_HANDLE, &image_index);
   assert(acquire_result == VK_SUCCESS || acquire_result == VK_SUBOPTIMAL_KHR);

   VkCommandBufferBeginInfo begin = {
      .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
   };
   check(vkBeginCommandBuffer(command, &begin));
   VkImageMemoryBarrier barrier = {
      .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
      .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
      .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
      .newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
      .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
      .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
      .image = images[image_index],
      .subresourceRange = {
         .aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
         .levelCount = 1,
         .layerCount = 2,
      },
   };
   vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                        VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0, NULL,
                        1, &barrier);
   bool swap_eyes = getenv("VULKAN_STEREO_SWAP_EYES") != NULL;
   VkClearColorValue colors[2] = {
      swap_eyes ? (VkClearColorValue){{0, 1, 0, 1}} : (VkClearColorValue){{1, 0, 0, 1}},
      swap_eyes ? (VkClearColorValue){{0, 0, 0.78f, 1}} : (VkClearColorValue){{0.78f, 0, 0, 1}},
   };
   for (uint32_t layer = 0; layer < 2; layer++)
      vkCmdClearColorImage(command, images[image_index],
                           VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &colors[layer],
                           1, &(VkImageSubresourceRange) {
                              VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, layer, 1 });
   barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
   barrier.dstAccessMask = 0;
   barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
   barrier.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
   vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT,
                        VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, NULL, 0,
                        NULL, 1, &barrier);
   check(vkEndCommandBuffer(command));

   VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
   VkSubmitInfo submit = {
      .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
      .waitSemaphoreCount = 1,
      .pWaitSemaphores = &acquire,
      .pWaitDstStageMask = &wait_stage,
      .commandBufferCount = 1,
      .pCommandBuffers = &command,
      .signalSemaphoreCount = 1,
      .pSignalSemaphores = &present,
   };
   check(vkQueueSubmit(queue, 1, &submit, VK_NULL_HANDLE));
   VkPresentInfoKHR present_info = {
      .sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR,
      .waitSemaphoreCount = 1,
      .pWaitSemaphores = &present,
      .swapchainCount = 1,
      .pSwapchains = &swapchain,
      .pImageIndices = &image_index,
   };
   VkResult present_result = vkQueuePresentKHR(queue, &present_info);
   assert(present_result == VK_SUCCESS || present_result == VK_SUBOPTIMAL_KHR);
   check(vkQueueWaitIdle(queue));
   usleep(100000);
   }
   const char *hold = getenv("VULKAN_STEREO_HOLD_SECONDS");
   if (hold)
      sleep(strtoul(hold, NULL, 10));

   puts(getenv("VULKAN_STEREO_SWAP_EYES") ? "PASS: Vulkan stereo deliberate eye swap" :
        "PASS: Vulkan stereo layers and packed present");
   vkDestroySemaphore(device, present, NULL);
   vkDestroySemaphore(device, acquire, NULL);
   vkDestroyCommandPool(device, pool, NULL);
   free(images);
   vkDestroySwapchainKHR(device, swapchain, NULL);
   vkDestroyDevice(device, NULL);
   vkDestroySurfaceKHR(instance, surface, NULL);
   vkDestroyInstance(instance, NULL);
   xcb_destroy_window(conn, window);
   xcb_disconnect(conn);
   return 0;
}
