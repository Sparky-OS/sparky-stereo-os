/* SPDX-License-Identifier: MIT
 * What a one-layer Vulkan X11 presentation does when the swapchain and the window differ in size.
 * An X11 top-level of WIN_W x WIN_H, a one-layer swapchain of EXT_W x EXT_H (default: the surface's currentExtent),
 * FRAMES presents of a picture whose left half is red and right half blue, each with a white 40x40 square that moves
 * 16 px a frame. At frame RESIZE_AT the window is resized to RESIZE_W x WIN_H. Each present's VkResult and the
 * window's geometry are printed, so a run tells whether the driver accepts an extent other than the window's,
 * whether it reports VK_ERROR_OUT_OF_DATE_KHR or VK_SUBOPTIMAL_KHR when the window changes, and (under xtrace) which
 * X requests carry the picture.
 * Build: cc -O1 -Wall -o vk-extent-probe vk-extent-probe.c -lvulkan -lxcb
 * LAYERS=2 asks for a swapchain of two image layers whatever maxImageArrayLayers says (a program that asks anyway);
 * CHILD=1 puts the window inside a 1000x700 top-level, 100,50 from its corner.
 * Environment: WIN_W WIN_H EXT_W EXT_H FRAMES RESIZE_AT RESIZE_W HOLD_S LAYERS CHILD
 *   VK_VENDOR (0x10de NVIDIA, 0x1002 AMD, 0x10005 lavapipe) */
#define VK_USE_PLATFORM_XCB_KHR
#include <vulkan/vulkan.h>
#include <xcb/xcb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CHECK(x) do { VkResult r_ = (x); if (r_ != VK_SUCCESS) { fprintf(stderr, "%s failed: %d\n", #x, r_); exit(1); } } while (0)

static int env(const char *name, int fallback)
{
   const char *s = getenv(name);
   return s && *s ? (int)strtol(s, NULL, 0) : fallback;
}

int main(void)
{
   setvbuf(stdout, NULL, _IOLBF, 0);
   const int win_w = env("WIN_W", 800), win_h = env("WIN_H", 600);
   xcb_connection_t *conn = xcb_connect(NULL, NULL);
   if (xcb_connection_has_error(conn)) { fprintf(stderr, "no X server\n"); return 1; }
   xcb_screen_t *screen = xcb_setup_roots_iterator(xcb_get_setup(conn)).data;
   xcb_window_t window = xcb_generate_id(conn), top = window;
   uint32_t values[] = { screen->black_pixel };
   if (env("CHILD", 0)) {
      xcb_create_window(conn, XCB_COPY_FROM_PARENT, top, screen->root, 0, 0, 1000, 700, 0,
                        XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL, values);
      window = xcb_generate_id(conn);
      xcb_create_window(conn, XCB_COPY_FROM_PARENT, window, top, 100, 50, win_w, win_h, 0,
                        XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL, values);
      xcb_map_window(conn, window);
   } else {
      xcb_create_window(conn, XCB_COPY_FROM_PARENT, window, screen->root, 0, 0, win_w, win_h, 0,
                        XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL, values);
   }
   xcb_change_property(conn, XCB_PROP_MODE_REPLACE, top, XCB_ATOM_WM_NAME, XCB_ATOM_STRING, 8, 14, "vk-extent-probe");
   xcb_map_window(conn, top);
   xcb_flush(conn);
   usleep(500000);

   const char *ext[] = { VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_XCB_SURFACE_EXTENSION_NAME };
   VkApplicationInfo app = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .apiVersion = VK_API_VERSION_1_1 };
   VkInstanceCreateInfo ici = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &app,
                                .enabledExtensionCount = 2, .ppEnabledExtensionNames = ext };
   VkInstance instance;
   CHECK(vkCreateInstance(&ici, NULL, &instance));
   VkXcbSurfaceCreateInfoKHR sci = { .sType = VK_STRUCTURE_TYPE_XCB_SURFACE_CREATE_INFO_KHR, .connection = conn,
                                     .window = window };
   VkSurfaceKHR surface;
   CHECK(vkCreateXcbSurfaceKHR(instance, &sci, NULL, &surface));
   uint32_t count = 8;
   VkPhysicalDevice physicals[8], physical = VK_NULL_HANDLE;
   CHECK(vkEnumeratePhysicalDevices(instance, &count, physicals));
   const uint32_t vendor = (uint32_t)env("VK_VENDOR", 0);
   for (uint32_t i = 0; i < count && !physical; i++) {
      VkPhysicalDeviceProperties p;
      vkGetPhysicalDeviceProperties(physicals[i], &p);
      if (!vendor || p.vendorID == vendor) {
         physical = physicals[i];
         printf("device %s\n", p.deviceName);
      }
   }
   if (!physical) { fprintf(stderr, "no device of vendor 0x%x\n", vendor); return 1; }
   float priority = 1;
   VkDeviceQueueCreateInfo qci = { .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, .queueFamilyIndex = 0,
                                   .queueCount = 1, .pQueuePriorities = &priority };
   const char *dext[] = { VK_KHR_SWAPCHAIN_EXTENSION_NAME };
   VkDeviceCreateInfo dci = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, .queueCreateInfoCount = 1,
                              .pQueueCreateInfos = &qci, .enabledExtensionCount = 1, .ppEnabledExtensionNames = dext };
   VkDevice device;
   CHECK(vkCreateDevice(physical, &dci, NULL, &device));
   VkQueue queue;
   vkGetDeviceQueue(device, 0, 0, &queue);
   VkSurfaceCapabilitiesKHR caps;
   CHECK(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   printf("caps current %ux%u min %ux%u max %ux%u layers %u\n", caps.currentExtent.width, caps.currentExtent.height,
          caps.minImageExtent.width, caps.minImageExtent.height, caps.maxImageExtent.width, caps.maxImageExtent.height,
          caps.maxImageArrayLayers);
   const uint32_t ew = (uint32_t)env("EXT_W", (int)caps.currentExtent.width);
   const uint32_t eh = (uint32_t)env("EXT_H", (int)caps.currentExtent.height);
   VkSwapchainCreateInfoKHR ci = {
      .sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR, .surface = surface, .minImageCount = 3,
      .imageFormat = VK_FORMAT_B8G8R8A8_UNORM, .imageColorSpace = VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
      .imageExtent = { ew, eh }, .imageArrayLayers = (uint32_t)env("LAYERS", 1), .imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT,
      .imageSharingMode = VK_SHARING_MODE_EXCLUSIVE, .preTransform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR,
      .compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR, .presentMode = VK_PRESENT_MODE_FIFO_KHR, .clipped = VK_TRUE,
   };
   VkSwapchainKHR swapchain;
   VkResult made = vkCreateSwapchainKHR(device, &ci, NULL, &swapchain);
   printf("create %ux%u layers %d on window %dx%d: %d\n", ew, eh, env("LAYERS", 1), win_w, win_h, made);
   if (made != VK_SUCCESS)
      return 2;
   VkImage images[8];
   count = 8;
   CHECK(vkGetSwapchainImagesKHR(device, swapchain, &count, images));
   VkBufferCreateInfo bci = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = (VkDeviceSize)ew * eh * 4,
                              .usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT };
   VkBuffer upload;
   CHECK(vkCreateBuffer(device, &bci, NULL, &upload));
   VkMemoryRequirements req;
   vkGetBufferMemoryRequirements(device, upload, &req);
   VkPhysicalDeviceMemoryProperties mp;
   vkGetPhysicalDeviceMemoryProperties(physical, &mp);
   uint32_t type = UINT32_MAX;
   const VkMemoryPropertyFlags host = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
   for (uint32_t i = 0; i < mp.memoryTypeCount && type == UINT32_MAX; i++)
      if ((req.memoryTypeBits & (1u << i)) && (mp.memoryTypes[i].propertyFlags & host) == host)
         type = i;
   VkMemoryAllocateInfo mai = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .allocationSize = req.size,
                                .memoryTypeIndex = type };
   VkDeviceMemory memory;
   CHECK(vkAllocateMemory(device, &mai, NULL, &memory));
   CHECK(vkBindBufferMemory(device, upload, memory, 0));
   uint32_t *pixels;
   CHECK(vkMapMemory(device, memory, 0, VK_WHOLE_SIZE, 0, (void **)&pixels));
   VkCommandPoolCreateInfo pci = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                   .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT };
   VkCommandPool pool;
   CHECK(vkCreateCommandPool(device, &pci, NULL, &pool));
   VkCommandBufferAllocateInfo cai = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .commandPool = pool,
                                       .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1 };
   VkCommandBuffer command;
   CHECK(vkAllocateCommandBuffers(device, &cai, &command));
   VkSemaphoreCreateInfo semi = { .sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO };
   VkSemaphore acquired, rendered;
   CHECK(vkCreateSemaphore(device, &semi, NULL, &acquired));
   CHECK(vkCreateSemaphore(device, &semi, NULL, &rendered));
   VkFenceCreateInfo fci = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
   VkFence fence;
   CHECK(vkCreateFence(device, &fci, NULL, &fence));

   const int frames = env("FRAMES", 120), resize_at = env("RESIZE_AT", -1), resize_w = env("RESIZE_W", 2 * win_w);
   for (int frame = 1; frame <= frames; frame++) {
      if (frame == resize_at) {
         uint32_t size[] = { (uint32_t)resize_w, (uint32_t)win_h };
         xcb_configure_window(conn, window, XCB_CONFIG_WINDOW_WIDTH | XCB_CONFIG_WINDOW_HEIGHT, size);
         xcb_flush(conn);
         usleep(200000);
      }
      const uint32_t mark = 20 + (frame * 16) % (ew / 2 - 80);
      for (uint32_t y = 0; y < eh; y++)
         for (uint32_t x = 0; x < ew; x++) {
            uint32_t c = x < ew / 2 ? 0xffff0000 : 0xff0000ff;
            uint32_t lx = x < ew / 2 ? x : x - ew / 2;
            if (lx >= mark && lx < mark + 40 && y >= 20 && y < 60)
               c = 0xffffffff;
            pixels[y * ew + x] = c;
         }
      uint32_t index;
      VkResult r = vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &index);
      if (r != VK_SUCCESS && r != VK_SUBOPTIMAL_KHR) { printf("frame %d acquire %d\n", frame, r); break; }
      VkCommandBufferBeginInfo begin = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO };
      CHECK(vkResetCommandBuffer(command, 0));
      CHECK(vkBeginCommandBuffer(command, &begin));
      VkImageMemoryBarrier b = { .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
         .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED, .newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
         .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
         .image = images[index], .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 } };
      vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0, NULL, 1, &b);
      VkBufferImageCopy copy = { .imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 }, .imageExtent = { ew, eh, 1 } };
      vkCmdCopyBufferToImage(command, upload, images[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
      b.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
      b.dstAccessMask = 0;
      b.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
      b.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
      vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, NULL, 0, NULL, 1, &b);
      CHECK(vkEndCommandBuffer(command));
      VkPipelineStageFlags stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
      VkSubmitInfo si = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .waitSemaphoreCount = 1, .pWaitSemaphores = &acquired,
                          .pWaitDstStageMask = &stage, .commandBufferCount = 1, .pCommandBuffers = &command,
                          .signalSemaphoreCount = 1, .pSignalSemaphores = &rendered };
      CHECK(vkQueueSubmit(queue, 1, &si, fence));
      VkPresentInfoKHR pi = { .sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR, .waitSemaphoreCount = 1,
                              .pWaitSemaphores = &rendered, .swapchainCount = 1, .pSwapchains = &swapchain,
                              .pImageIndices = &index };
      r = vkQueuePresentKHR(queue, &pi);
      CHECK(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX));
      CHECK(vkResetFences(device, 1, &fence));
      xcb_get_geometry_reply_t *g = xcb_get_geometry_reply(conn, xcb_get_geometry(conn, window), NULL);
      if (frame <= 3 || r != VK_SUCCESS || frame == resize_at || frame == resize_at + 1 || frame % 30 == 0)
         printf("frame %d present %d window %ux%u\n", frame, r, g ? g->width : 0, g ? g->height : 0);
      free(g);
      if (r != VK_SUCCESS && r != VK_SUBOPTIMAL_KHR) break;
      usleep(16000);
   }
   CHECK(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   printf("caps after current %ux%u\n", caps.currentExtent.width, caps.currentExtent.height);
   sleep((unsigned)env("HOLD_S", 0));
   vkDeviceWaitIdle(device);
   return 0;
}
