---
layout: post
title: "Holographic Glasses for Virtual Reality"
date: 2022-10-23
---

Jonghyun Kim, Manu Gopakumar, Suyeon Choi, Yifan Peng, Ward Lopes, Gordon Wetzstein 

SIGGRAPH 2022

## Summary:

Since holography directly aims to reconstruct the original 3D irradiance field, it naturally provides depth cues to overcome the dizzy problem binocular VR struggling. However, due to the complicated optical setting, large physical occupancy, and difficult phase mask optimization, there is still no public holographic display for near-eye usage. This paper proposes and builds up a near-eye holographic display VR prototype in publicly. Even though the final prototye only covered monocular results.

The system is composed of several components for its hardware.

**Pupil-replicating waveguide:**

Normal holographic settings require (partially) coherent light and often use a beam splitter cube or off-axis illumination, which take a lot space. This prototype adopts a pupil-replicating waveguide for conventional AR display and overcomes the non-planer/spherical wavefront issue by deep-learning CGH methods.

**Holographic near-eye display**

A phase-only SLM creates 2D/3D image at small distance and mounted directly on the wavefront without air gap to shrink down the size.

**Geometric phase lens and polarization control**

The geometric phase lens can act as a positive lens for a specific circular polarized light using diffraction. Since it is flat, it could make the system thinner. The polarization control (Quarter Wave Plate) could transform the linear polarized light used in SLM to circular polarized light.  

The light path inside a monocular glass would be:

Coherent light enters the waveguide and go coupled out with a angle of theta_c. It then passes through the linear polarizer to polarize its phase. The coherent light is then modulated by the SLM with the pattern we defined. The light then reflects back to the waveguide. Only small portion of the light will etner into the waveguide but most of the light will go out and hit the Quater Wave Plate to make the light right circularly polarized (RCP). The geometric phase lens will focus the RCP to the eye.
## Why Good:
1.	This work is a pioneer exploration on near-eye VR prototype adopting holographic technology.

2.	This work is a huge step toward ultra-thin all-day-wearable VR which is obviously the next generation of the smart devices everyone would have.

## Possible Follow-On:

There is a tradeoff between the SLM size and the field of view, SLM pixel pitch size with the eye box size. So the key limit for this system is the SLM’s manufacture. Also the paper hasn’t covered the design of the following aspects:

1.	Real-time phase pattern calculation is impossible without good GPU which is not included in the prototype.

2.	Speckle could be reduced by using partial-coherent light

3.	Eye tracking and pupil diameter measurement system is not included in the prototype.

4.	The 3-color coherent light can be formed in a more compact form to shrink down the size.
