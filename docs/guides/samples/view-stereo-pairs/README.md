# Sample pairs for "View stereo pairs and photos on any monitor"

Two stereo pairs you may use, copy and share, each pinned by address, hash and licence.
Open them in [the guide](../../view-stereo-pairs-and-photos.en.md).

## A topographic pair from an elevation model

**File:** [rainier-elevation-pair.mpo](rainier-elevation-pair.mpo), an MPO with two pictures of 800 by 700, the left eye first.
SHA-256 `e67f880b7b5e4b34138628cf0a84776de5f5226258b912c6d805c7f0b0820df5`.

**What it is:** the country around Mount Rainier (longitude -121.85 to -121.65, latitude 46.78 to 46.92) drawn as shaded relief, tinted by height, once for each eye.
High ground has crossed disparity and comes in front of the screen, low ground sinks behind it; the summit and the lowest ground differ by 12 px between the eyes at 800 px per eye.
Rendered by [render-elevation-pair.py](render-elevation-pair.py) with a maximum disparity of 6 px, then written as an MPO by Align stereo pair.

**Data:** the U.S. Geological Survey's 3D Elevation Program (3DEP), asked for this area from the USGS National Map service at 800 by 700 samples as 32-bit float:

```
https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?bbox=-121.85,46.78,-121.65,46.92&bboxSR=4326&imageSR=4326&size=800,700&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&f=image
```

The answer of 17 November 2026 has SHA-256 `7b51a07b267ee81e1fc81df9a986afd0cdb19bbf2b9f70b1f5aa74cfd960421b`; the service may answer another picture later, which gives another pair.

**Licence:** "USGS-authored or produced data and information are considered to be in the U.S. Public Domain" ([USGS, Copyrights and Credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits)).
Credit: elevation data from the U.S. Geological Survey.

## A pair taken with a Nintendo 3DS

**Files:** the left picture and the right picture, linked from their page on Wikimedia Commons and not copied here:
[left](https://upload.wikimedia.org/wikipedia/commons/6/6f/Friedrich-Wilhelm-Stollen_20130820_Stereo_HNI_0004-L.jpg), SHA-256 `c76ad28f55a7a7350f5b6324233009687c378240fd71c677c77301e2b54d1863`;
[right](https://upload.wikimedia.org/wikipedia/commons/9/9e/Friedrich-Wilhelm-Stollen_20130820_Stereo_HNI_0004-R.jpg), SHA-256 `9921492f60c47b3bbe639426855fb327f29f5d5a8532f16927b32b665edb8d76`.
Each is 640 by 480.

**What it is:** a photograph of 20 August 2013 from the camera of a Nintendo 3DS, the two views taken out of the camera's MPO file.
Select both in Dolphin and choose **Align stereo pair, Save as MPO, first picture is the left eye** to make the MPO again.

**Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0), by PantheraLeo1359531.
A copy or an adaptation carries the same licence and this credit.
