/* SPDX-License-Identifier: MIT */
/* Prints every event libspnav delivers, summed per second; a test client for a daemon and a device. */
#include <stdio.h>
#include <spnav.h>
int main(void)
{
	spnav_event ev; long n = 0, sum[6] = {0}; char name[256] = "";
	if (spnav_open() == -1) { printf("spnav_open failed: no daemon on the socket\n"); return 1; }
	printf("connected, protocol %d, devices known to the daemon: ", spnav_protocol());
	if (spnav_dev_name(name, sizeof name) >= 0) printf("%s\n", name); else printf("(none)\n");
	fflush(stdout);
	while (spnav_wait_event(&ev)) {
		if (ev.type == SPNAV_EVENT_MOTION) {
			sum[0] += ev.motion.x; sum[1] += ev.motion.y; sum[2] += ev.motion.z;
			sum[3] += ev.motion.rx; sum[4] += ev.motion.ry; sum[5] += ev.motion.rz; n++;
			if (n % 10 == 0) { printf("motion events %ld, sums x %ld y %ld z %ld rx %ld ry %ld rz %ld\n", n, sum[0], sum[1], sum[2], sum[3], sum[4], sum[5]); fflush(stdout); }
		} else if (ev.type == SPNAV_EVENT_BUTTON) {
			printf("button %d %s (after %ld motion events, sums x %ld y %ld z %ld rx %ld ry %ld rz %ld)\n", ev.button.bnum, ev.button.press ? "pressed" : "released", n, sum[0], sum[1], sum[2], sum[3], sum[4], sum[5]); fflush(stdout);
		}
	}
	return 0;
}
