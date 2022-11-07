---
layout: post
title: "Hogel-free Holography"
date: 2022-11-06
---

Praneeth Chakravarthula, Ethan Tseng, Henry Fuchs, Felix Heide

ACM Transactions on Graphics 2022

## Summary of Contribution:
This paper provides a new paradigm to compute the phase map of a 3D scene for computer generated holography (CGH) research by taking the RGB-D light field images of a scene as input and estimating its emanating wavefront. 

From my point of view, the value of this paper is limitless since it finally opens the gate of the inverse problem of the CGH, which means a way to use physical measurement tools (a depth light field camera) to measure and estimate the wavefront on the wave recorder plane and inversely trace back to the original scene plane to get what phase information is required for generating such scene. The work closes the loop of  the classical computational imaging pipeline for CGH and you can imagine this enables such ‘3D Recording and Replay’ application for hologram based near-eye smart AR devices. The computer generated hologram could expand to camera measured hologram.

Let alone the possible applications on the measuring side, let’s focus on the generating side this paper aimed to. Ideally, compared with other CGH approaches like point-based, polygon-based, layer-based, and hogel-based methods, this work directly models wavefront of the original scene from the light field and depth information and thus getting rid-off the approximation brought by the modeling primitives. I would prefer to call it the wavefront-based method. 

The problems of current CGH methods are facing can be roughly split into two groups: the artifacts problems brought by the imperfect simulation of the original wavefront and the resolution problem brought by the limited space-bandwidth product of existing spatial light modulator (SLMs). Even though this paper achieves both improvement on these two problems, we need to think and understand clearly that the source of the magics actually comes from different parts of the model.

For the artifact problems, the wavefront based method itself doesn’t promise any solutions to the most of current artifacts problems other CGH methods are facing, for examples, the parallax and defocus inaccuracy. The only exception is its ability to avoid cross talk between the independent primitive wave fronts when the axial extent of the distribution increased. The reason why proposed work could compute physically accurate hologram lies in the physical correctness guaranteed by the input light field image and the input depth information. If the input light field images are generated incorrectly, there is no way for this model alone to correct. It would be interesting to think with physically correct light field information, could other primitive based modelling methods also achieve correct rendering?

For the resolution problems, this work doesn’t aim to solve this even though the authors argued that it overcomes the fundamental spatio-angular resolution problem to sterogram approaches. We need to understand the resolution is improved compared with other sterogram methods similar to light field camera, the reason is that those methods do discrete sampling with approximation on the hologram plane rather than on the source scene. However, the proposed method directly computed the original continuous source wavefront which lead to higher spatial resolution due to no spatio-angular tradeoff. But the final display resolution is still depends on the space-bandwidth product of the SLM, which is same as the other primitive based methods.

The key idea of the computation for this work is based on the assumption/fact that the light field angular rays are nothing but a coarsely sampled continuous wavefront. Thus, the wavefront on the wavefront recorder plane can be recovered. Since the input also includes the depth information, it makes the inverse of the wavefront propagation possible. The specific computation process can be summarized as below, including the un-reduced thought process:

1.	Naively, we want to find the phase mask on the hologram plane, that for all the different light field angular perspective, the sampled propagation intensity image could be as similar as the ground truth light field images.

2.	To avoid the sum of the error term of all light field perspectives,  the objective function is rewritten into wave domain. To minimize the wavefront difference between the complex wave on wave recorder plane and the sum of the wavefronts from different light field perspectives. The wavefront of a single perspective is modeled as the inverse mapping of the square root of the light field intensity with an unknown phase.

3.	The sampling function in the step 1 which maps the complex wavefront to a given angular light field views is called Windowed Fourier Transform (WFT).

4.	The light field inversion described in step 2 can be naively written as inverting the WFT in the frequency domain. However, the intensity information is missing in light field intensity images. To alleviate this ill-posed inversion, the phase information of the light field image is defined by the depth map. Similar to ToF idea.

5.	The loss function in step 2 also contains the amplitude information of the hologram plane wavefront, which is unable to applied on current phase-only SLMs. Notice the fact that the different initial phases could propagate to different intensity distribution in different distance.  The paper thus converts minimizing the phase amplitude difference on wave recorder plane to minimize the propagation difference between the phase only light field measured wavefront and the estimated source plane wavefront in an arbitrary long continuous volume after the WR plane. The ground truth here is the measured light field wavefront and its propagation in that volume only calculate once. The estimated phase on the source plane is iteratively improved by the gradient descent of the loss between the ground truth and the propagation result.

6.	The loss function here is a compound function of L2 loss, SSIM loss, VGG-19 perception loss and the Waston FFT loss to make sure the propagation result is similar enough.

## Novelty:
The novelty of the work is clearly on the display. The development motivation is clear and the ways to overcome the barriers toward that preset goal are also skillful. It provides at least three independent useful template solution to common CGH problems for later works to reference:
1.	How to convert the light field image with depth to the complex wavefront.

2.	How to convert the amplitude + phase complex matrix in the loss function to a phase-only matrix problem by minimizing the future propagation result in a continuous volume, which is especially useful to existing SLM problem.

3.	How to better measure the difference between two wave propagation results. 

Besides the solution templates, the wavefront-based method it proposed could also be marked as an independent paradigm for CGH problems with its strengths of physical correctness and no spatio-angular tradeoff.

## Potential Impact/Technical Merit:

On the application level, it also open the door of the inverse wavefront estimation from light field image measurement in CGH. The possibility of directly measuring the real world shape wavefront is open, even though the current measuring tools is still inaccurate. Undoubtfully, it will flourish the AR research for hologram based near eye devices.

## Questions:
* How to better decide the sampling number for wave propagation in a continuous volume? What is the relationship between the sampling number and the size of the phase mask?

* How the angular sampling density for light field image influence the final hologram quality?

* How double-phase encoding conversion perform in this case? Why not use current differentiable amplitude phase to phase-only method to do the phase mask optimization?

* How could camera-in-the-loop calibration idea be combined in this work?

