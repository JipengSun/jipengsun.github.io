---
layout: post
title: "Cascaded Diffusion for Super-resolution Image Generation"
date: 2022-11-28
---

**Cascaded Diffusion Models for High Fidelity Image Generation**

Jonathan Ho, Chitwan Saharia, William Chan, David J. Fleet, Mohammad Norouzi, Tim Salimans

Google Tech Report 2021

## Summary:

This paper explained the up-sampling architecture implementation in diffusion models. Upsampling a general approach to be used in training photorealistic deep generative models. Previously, there are many different up-sampling frameworks for other deep generative models(eg. BigGAN-deep for GAN, VQ-VAE 2 for VAE, etc.) This work’s architecture is latter adopted in Google ImagEN which further showcased its generalization on the large real-world datasets.

The main contribution of the paper is proposing the cascading structure, which is a technique to model high resolution data from separately trained models at multiple resolution. A based model generates low resolution samples, followed by super-resolution models that up-sample low resolution samples into high resolution samples. The most effective trick this paper found to alleviates the ‘exposure bias’ or ‘cascading problem’ in sequence model is to apply strong data augmentation to the conditioning input of each super-resolution model. A major benefit to training a cascading pipeline over  training a standard model at the highest resolution is that most of the modeling capacity can be dedicated to low resolutions, which empirically are the most important for sample quality, and training and sampling at low resolutions tents to be the most computationally efficient. Besides, cascading allows the individual models to be trained independently with specific architecture choices.

There are two conditioning ways to add conditional input into the diffusion model: One is the scalar conditioning which adds embeddings (timestep or class label) into intermediate layers of the network; another is the lower resolution image conditioning is provided by channel wise concatenation of the low resolution image with the reverse process input x_t processed by bilinear or bicubic upsampling to the desired resolution.

The paper introduced three augmentation methods which respectively perform best in their specific use cases. 

1. Blurring augmentation is used to apply amount of Gaussian blur on the low resolution input. The paper found that it is most effective to images with resolution 128\*128 and 256\*256. 50% of the examples are blurred for the training stage to force the diffusion model learn better from noised input and no blurring in the inference stage; 

2. Truncated conditioning augmentation means stopping the reverse sampling process early for the low resolution image generation at step s to get a more noised input to the following high-resolution model. It performs best at resolutions smaller than 128\*128. The best step number s is searched from different experiments. To avoid retraining the models, they amortized a single super-resolution model over uniform random s at training time. Because each possible truncation time corresponds to a distinct super-resolution task, the input of the super resolution block also has an extra time step s embedding; 

3. Non-truncated conditioning augmentations shares the same goal as truncated one, but the only difference is at sampling time. Instead of truncated the low resolution reverse process, it will sample the final low resolution image z_0 and then corrupt it using the forward process to get the early stopped z_s’. The motivation behind it is parallelization. In the truncated cases, to search all possible s value, it needs to store z_s for every model. However, if we do it in a non-truncated way, we can just store the z_0 for all models and do a computationally inexpensive forward process to get different z_s.

## Strength:

Adding reasonable noise to the low resolution input to force the super-resolution task more relied on the network itself rather than bi-linear interpolation operation is a correct direction to go and this paper provides three different ways to implement on diffusion models.

## Critique:

Even though they argued in the paper they will release the source code, it is still un-released now. Which makes it difficult to spread except the works in Google. Besides this paper, I also found other diffusion works are really brief on up-sampling models, which is confusing when comes down to implementation.
