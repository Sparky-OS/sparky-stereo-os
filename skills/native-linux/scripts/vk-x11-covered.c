/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#include <X11/Xlib.h>
#define VK_USE_PLATFORM_XCB_KHR
#define VK_USE_PLATFORM_XLIB_KHR
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
   uint32_t cx = 100, cy = 50, width = 800, height = 600;
   if (!strcmp(mode, "overflow")) { cx = 250; cy = 200; width = 300; height = 200; }
   xcb_connection_t *conn = xcb_connect(NULL, NULL);
   assert(conn && !xcb_connection_has_error(conn));
   const xcb_setup_t *setup = xcb_get_setup(conn);
   xcb_screen_iterator_t screen_iter = xcb_setup_roots_iterator(setup);
   xcb_screen_t *screen = screen_iter.data;

   xcb_window_t parent = xcb_generate_id(conn);
   uint32_t pvalues[] = {0x202020, XCB_EVENT_MASK_EXPOSURE};
   xcb_create_window(conn, XCB_COPY_FROM_PARENT, parent, screen->root, 100, 100, 1000, 700, 0,
                     XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, pvalues);
   xcb_window_t window = xcb_generate_id(conn);
   uint32_t values[] = {screen->black_pixel, XCB_EVENT_MASK_EXPOSURE};
   xcb_create_window(conn, XCB_COPY_FROM_PARENT, window, parent, cx, cy, width, height, 0, XCB_WINDOW_CLASS_INPUT_OUTPUT,
                     screen->root_visual, XCB_CW_BACK_PIXEL | XCB_CW_EVENT_MASK, values);
   if (getenv("TOPLEVEL")) {
      xcb_destroy_window(conn, window);
      window = parent;
      uint32_t size[] = {width, height};
      xcb_configure_window(conn, parent, XCB_CONFIG_WINDOW_WIDTH | XCB_CONFIG_WINDOW_HEIGHT, size);
   }
   xcb_window_t cover = xcb_generate_id(conn);
   uint32_t grey = 0x808080;
   xcb_create_window(conn, XCB_COPY_FROM_PARENT, cover, window, 30, height/2, 60, 60, 0,
                     XCB_WINDOW_CLASS_INPUT_OUTPUT, screen->root_visual, XCB_CW_BACK_PIXEL, &grey);
   if (!getenv("UNCOVERED")) xcb_map_window(conn, cover);
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
      VK_KHR_SURFACE_EXTENSION_NAME, getenv("XLIB") ? VK_KHR_XLIB_SURFACE_EXTENSION_NAME : VK_KHR_XCB_SURFACE_EXTENSION_NAME,
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
   Display *xdisplay = NULL;
   if (getenv("XLIB")) {
      xdisplay = XOpenDisplay(NULL); assert(xdisplay);
      VkXlibSurfaceCreateInfoKHR xlib = { .sType=VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR,
         .dpy=xdisplay, .window=window };
      check(vkCreateXlibSurfaceKHR(instance,&xlib,NULL,&surface));
   } else {
      check(vkCreateXcbSurfaceKHR(instance, &surface_info, NULL, &surface));
   }

   uint32_t physical_count = 0;
   check(vkEnumeratePhysicalDevices(instance, &physical_count, NULL));
   assert(physical_count > 0);
   VkPhysicalDevice *physical_devices = calloc(physical_count, sizeof(*physical_devices));
   check(vkEnumeratePhysicalDevices(instance, &physical_count, physical_devices));
   VkPhysicalDevice physical = physical_devices[0];
   if (getenv("VK_VENDOR")) {
      uint32_t wanted=strtoul(getenv("VK_VENDOR"),NULL,0); physical=VK_NULL_HANDLE;
      for(uint32_t i=0;i<physical_count;i++) {
         VkPhysicalDeviceProperties info; vkGetPhysicalDeviceProperties(physical_devices[i],&info);
         fprintf(stderr,"available=%s vendor=%04x\n",info.deviceName,info.vendorID);
         if(info.vendorID==wanted) physical=physical_devices[i];
      }
      if(!physical) { fprintf(stderr,"requested Vulkan device unavailable\n"); return 7; }
   }
   free(physical_devices);
   VkPhysicalDeviceProperties physical_info;
   vkGetPhysicalDeviceProperties(physical, &physical_info);
   fprintf(stderr, "physical=%s vendor=%04x device=%04x\n", physical_info.deviceName, physical_info.vendorID, physical_info.deviceID);

   VkSurfaceCapabilitiesKHR caps;
   check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
   fprintf(stderr, "maxImageArrayLayers=%u extent=%ux%u\n", caps.maxImageArrayLayers, caps.currentExtent.width, caps.currentExtent.height);
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
      .presentMode = getenv("IMMEDIATE") ? VK_PRESENT_MODE_IMMEDIATE_KHR : VK_PRESENT_MODE_FIFO_KHR,
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
      .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
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
   VkBuffer upload;
   VkBufferCreateInfo bi = { .sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
      .size=(VkDeviceSize)width*height*8, .usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
      .sharingMode=VK_SHARING_MODE_EXCLUSIVE };
   check(vkCreateBuffer(device, &bi, NULL, &upload));
   VkMemoryRequirements req; vkGetBufferMemoryRequirements(device, upload, &req);
   VkPhysicalDeviceMemoryProperties mp; vkGetPhysicalDeviceMemoryProperties(physical, &mp);
   uint32_t mt=UINT32_MAX;
   for (uint32_t i=0;i<mp.memoryTypeCount;i++)
      if ((req.memoryTypeBits & (1u<<i)) && (mp.memoryTypes[i].propertyFlags &
          (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
          (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) { mt=i; break; }
   assert(mt!=UINT32_MAX);
   VkMemoryAllocateInfo mi={ .sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,.allocationSize=req.size,.memoryTypeIndex=mt };
   VkDeviceMemory memory; check(vkAllocateMemory(device,&mi,NULL,&memory));
   check(vkBindBufferMemory(device,upload,memory,0));
   uint32_t *pixels; check(vkMapMemory(device,memory,0,VK_WHOLE_SIZE,0,(void**)&pixels));
   int frames = getenv("FRAMES") ? atoi(getenv("FRAMES")) : 200;
   int still = getenv("STILL_AT") ? atoi(getenv("STILL_AT")) : -1;
   struct timespec before, after; clock_gettime(CLOCK_MONOTONIC,&before);
   for (int frame=1; frame<=frames; frame++) {
      if (frame == still) break;
      if (getenv("COVER_AT") && frame == atoi(getenv("COVER_AT"))) xcb_map_window(conn, cover);
      if (getenv("UNCOVER_AT") && frame == atoi(getenv("UNCOVER_AT"))) xcb_unmap_window(conn, cover);
      if (getenv("CHILD_PAINT_AT") && frame == atoi(getenv("CHILD_PAINT_AT"))) {
         uint32_t yellow=0xc0c000;
         xcb_change_window_attributes(conn, cover, XCB_CW_BACK_PIXEL, &yellow);
         xcb_clear_area(conn, false, cover, 0, 0, 0, 0);
      }
      xcb_flush(conn);
      int mark=20+(frame*16)%(width-80);
      for (uint32_t eye=0;eye<2;eye++) for (uint32_t y=0;y<height;y++) for(uint32_t x=0;x<width;x++) {
         uint32_t c=eye?0xff0000ff:0xffff0000;
         if(x>=width/4 && x<3*width/4 && y>=height/4 && y<3*height/4)c=0xff00ff00;
         if(x>=(uint32_t)mark && x<(uint32_t)mark+40 && y>=20 && y<60)c=0xffffffff;
         pixels[(eye*height+y)*width+x]=c;
      }

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
   VkBufferImageCopy regions[2] = {0};
   for(uint32_t eye=0;eye<2;eye++) {
      regions[eye].bufferOffset=(VkDeviceSize)eye*width*height*4;
      regions[eye].imageSubresource=(VkImageSubresourceLayers){VK_IMAGE_ASPECT_COLOR_BIT,0,eye,1};
      regions[eye].imageExtent=(VkExtent3D){width,height,1};
   }
   vkCmdCopyBufferToImage(command,upload,images[image_index],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,2,regions);
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
   if (frame<=10 || frame%10==0) {
      xcb_get_property_reply_t *p = xcb_get_property_reply(conn,
         xcb_get_property(conn, false, window, atom(conn, "_KDE_NET_WM_STEREO_CONTENT"), XCB_ATOM_CARDINAL, 0, 1), NULL);
      fprintf(stderr, "present %d declaration=%u\n", frame,
         p && p->format==32 && xcb_get_property_value_length(p)>=4 ? *(uint32_t *)xcb_get_property_value(p) : 0);
      free(p);
   }
   usleep((getenv("PERIOD_MS") ? atoi(getenv("PERIOD_MS")) : 50)*1000);
   }
   clock_gettime(CLOCK_MONOTONIC,&after);
   double elapsed=after.tv_sec-before.tv_sec+(after.tv_nsec-before.tv_nsec)*1e-9;
   fprintf(stderr,"frames=%d elapsed=%.6f fps=%.3f\n",frames,elapsed,frames/elapsed);
   const char *hold = getenv("HOLD_S");
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
   if(xdisplay) XCloseDisplay(xdisplay);
   xcb_destroy_window(conn, window);
   xcb_disconnect(conn);
   return 0;
}
