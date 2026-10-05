# Probe correction

![](images/media/image10.svg)

**Figure 1:** Geometry of the problem. Note: the spherical coordinates
$(\theta ’,\ \varphi ’)$ of the reference system associated with the
probe are equal to $(\theta,\  - \varphi)$ to those of the reference
system centered on the sampling
plane.

The geometry of the problem is shown in Fig. 1.

We consider an open-ended waveguide operating in its principal
Transverse Electric ($\mathrm{TE}_{10}$) mode, serving as a probe to sample the
field over a rectangular aperture at $z=z_0.$ By convention it
will be assumed that the antenna aperture is the antenna under test
(AUT) and is transmitting and the measurement probe is the receiver.

> [!NOTE]
>
> The angles $(\theta\ ’,\ \varphi\ ’)$ in the reference system centered with the probe are equal to $(\theta, - \ \varphi)$ of the spherical coordinate associated to the reference system centered on the sampling aperture.

The sampled field can be expressed in the form of an inverse Fourier
transform (IFT) as [[1]](#1)-[[3]](#3):

$$
\begin{equation}
\mathbf{b}\left( x,y,z = z_{0} \right)\mathbf{= \ }\frac{1}{(2\pi)^{2}}\int_{- \infty}^{\infty}{\int_{- \infty}^{\infty}{\overline{\overline{\mathbf{R}}}\left( k_{x}{,k}_{y} \right)} \bullet \mathbf{T}\left( k_{x}{,k}_{y} \right)e^{- jk_{z}z_{0}}e^{- jk_{x}x}e^{- jk_{y}y}{dk_{x}}{dk_{y}}}
\end{equation}
$$

with $\overline{\overline{\mathbf{R}}}\left( k_{x}{,k}_{y} \right)$ and
$\mathbf{T}\left( k_{x}{,k}_{y} \right)$ being the transfer function of
the receiving probe and transmitting AUT, respectively, as function of
the spectral wavenumber $k_{x}{,k}_{y}$, with
$k = \sqrt{{k_{x}}^{2} + {k_{y}}^{2}}$ being the wavenumber in free
space.

The FT of the sampled field is then given by [[1]](#1), [[2]](#2):

$$
\begin{equation}\mathbf{B}\left( k_{x}{,k}_{y} \right)\mathbf{=}\overline{\overline{\mathbf{R}}}\left( k_{x}{,k}_{y} \right) \bullet \mathbf{T}\left( k_{x}{,k}_{y} \right)e^{- jk_{z}z_{0}},
\end{equation}
$$

The FT of the sample field can also be expressed as:

$$
\begin{equation}
\begin{aligned}
\mathbf{B}\left( k_{x}{,k}_{y} \right) &= \int_{- \infty}^{\infty}{\int_{- \infty}^{\infty}{\mathbf{b}\left( x,y,z = z_{0} \right)}e^{jk_{x}x}e^{jk_{y}y}{dx}{dy}},
\end{aligned}
\end{equation}
$$

The transfer function or field aperture of the transmitting antenna is
then given from (2) by:

$$
\begin{equation}
\mathbf{T}\left( k_{x}{,k}_{y} \right)\mathbf{= \ }e^{jk_{z}z_{0}}{\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x}{,k}_{y} \right) \bullet \int_{- \infty}^{\infty}{\int_{- \infty}^{\infty}{\mathbf{b}\left( x,y,z = z_{0} \right)}e^{jk_{x}x}e^{jk_{y}y}{dx}{dy}},
\end{equation}
$$

or equivalently:
$$
\begin{equation}
\mathbf{T}\left( k_{x}{,k}_{y} \right)\mathbf{= \ }e^{jk_{z}z_{0}}{\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x}{,k}_{y} \right) \bullet \mathbf{B}\left( k_{x}{,k}_{y} \right).
\end{equation}
$$

Eqs. (4) and (5) allow to correct the sampled field from the probe
transfer function if
${\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x}{,k}_{y} \right)$
is known.

The correction can be applied directly to the radiated fields. The
radiated fields in a spherical coordinate system are given by

$$
\mathbf{E}(r,\theta,\phi) \approx \frac{jke^{- jkr}}{2\pi r}\mathbf{\ }e^{j\cos\theta k_z z_{0}}{\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x0}{,k}_{y0} \right) \bullet \mathbf{B}\left( k_{x0}{,k}_{y0} \right)
$$
or
$$
\begin{equation}
\begin{aligned}
\mathbf{E}(r,\theta,\phi) &\approx e^{j\cos\theta k_z z_{0}}{\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x0}{,k}_{y0} \right) \bullet \left( \frac{jke^{- jkr}}{2\pi r}\mathbf{B}\left( k_{x0}{,k}_{y0} \right) \right) \\
&= e^{j\cos\theta k_z z_{0}}{\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x0}{,k}_{y0} \right) \bullet \mathbf{E}_{\mathbf{NC}}(r,\theta,\phi)
\end{aligned}
\end{equation}
$$
where $k_{x0} = k\sin\theta\cos\phi{,\ \ k}_{y0} = k\sin\theta\sin\phi$.
$\mathbf{E}_{\mathbf{NC}}(r,\theta,\phi)$ is the radiated field derived
from the sampled field over the aperture without any correction or in
other words the field derived using the FT,
$\mathbf{B}\left( k_{x}{,k}_{y} \right).$ It is worth noting that
$\mathbf{E}_{\mathbf{NC}}(r,\theta,\phi)$ is here expressed as
$\mathbf{E}_{\mathbf{NC}}(r,\theta,\phi) = E_{\theta}\widehat{\theta} + E_{\phi}\widehat{\phi}$
and we derive the corrected $\widehat{\theta}$ and $\widehat{\phi}$ of
$\mathbf{E}(r,\theta,\phi).$

The reception matrix
$\overline{\overline{\mathbf{R}}}\left( k_{x0}{,k}_{y0} \right)$ can be
found by using the expressions of the field radiated by an open-ended
waveguide. It can be shown by reciprocity that for an antenna:

$$
\eta_{\mathrm{mode}}\mathbf{R}\left( k_{x0}{,k}_{y0} \right)\mathbf{= -}\eta\mathbf{T}\left( - k_{x0}{, - k}_{y0} \right)
$$

In which $\eta_{\mathrm{mode}}$ and $\eta$ are the characteristic impedance of
the mode feeding the antenna and the free space impedance. For an
open-ended waveguide, $\eta_{\mathrm{mode}}$ corresponds to the $\mathrm{TE}_{10}$ impedance
$\eta_{\mathrm{mode}} = \frac{k\eta}{k_{z}}$.

The function $\mathbf{T}\left( k_{x0}{,k}_{y0} \right)$ can be retrieved
by using the field radiated by an open-ended waveguide with the electric
field oriented along $\widehat{x}$ and $\widehat{y}$, to take into
account the two orientations of the probe while measuring the field. In
particular, the radiated field can be derived using [[3]](#3):

$$
\begin{equation}
\begin{aligned}
\mathbf{E}(r,\theta,\phi) &\approx \frac{jke^{- jkr}}{2\pi r}\mathbf{\ T}\left( k_{x0}{,k}_{y0} \right) \\
&= \frac{jke^{- jkr}}{2\pi r}\left( T_{\mathbf{\theta}}\left( k_{x0}{,k}_{y0} \right)\widehat{\theta} + T_{\mathbf{\phi}}\left( k_{x0}{,k}_{y0} \right)\widehat{\phi} \right)
\end{aligned}
\end{equation}
$$

For a waveguide with the electric field along $\widehat{y}$, the
radiated field is given by [[3]](#3):

$$
\begin{equation}E_{\theta}(r,\theta,\phi) \approx \frac{jke^{- jkr}}{2\pi r}C_{0}\left( \sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)
\end{equation}
$$
$$
\begin{equation}E_{\phi}(r,\theta,\phi) \approx \frac{jke^{- jkr}}{2\pi r}C_{0}\left( \cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)
\end{equation}
$$
where
$$
\begin{equation}
X = \frac{ka}{2}\sin\theta\cos\phi
\end{equation}
$$
$$
\begin{equation}
Y = \frac{kb}{2}\sin\theta\sin\phi
\end{equation}
$$
where $a$ is the length of the aperture in the cross-pol dimension, $b$ is the length of the aperture in the co-pol dimension, and $C_{0}$ a normalization factor.

For a waveguide with the electric field along $\widehat{x}$, the
radiated field is given by [[3]](#3):

$$
\begin{equation}E_{\theta}(r,\theta,\phi) \approx \frac{jke^{- jkr}}{2\pi r}C_{0}\left( \cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)
\end{equation}
$$

$$
\begin{equation}
E_{\phi}(r,\theta,\phi) \approx \frac{jke^{- jkr}}{2\pi r}C_{0}\left( \mathbf{-}\cos\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)
\end{equation}
$$

The reception matrix
$\overline{\overline{\mathbf{R}}}\left( k_{x0}{,k}_{y0} \right)$
becomes:

$$
\begin{equation}
\begin{aligned}
\overline{\overline{\mathbf{R}}}\left( k_{x0}{,k}_{y0} \right) &= - \frac{\eta}{\eta_{\mathrm{mode}}}C_{0}\begin{bmatrix}
\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \mathbf{-}\cos\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}
\end{bmatrix}\\

&= - C_{1}
\begin{bmatrix}
\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \mathbf{-}\cos\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}
\end{bmatrix}
\end{aligned}
\end{equation}
$$
in which
$C_{1}$=$\frac{\eta}{\eta_{\mathrm{mode}}}C_{0}.\ {\overline{\overline{\mathbf{R}}}}^{- 1}\left( k_{x0}{,k}_{y0} \right)$
is then given by:
$$
\begin{equation}
{\overline{\overline{\mathbf{R}}}}^{- 1} = - \frac{C_{1}}{\det(\overline{\overline{\mathbf{R}}})}\begin{bmatrix}
  {- cos}\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \mathbf{-}\cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
  \mathbf{-}\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}
  \end{bmatrix}
\end{equation}
$$
where
$$
\begin{equation}
\begin{aligned}
\det\left( \overline{\overline{\mathbf{R}}} \right) &= &- \sin \phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}\cos\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
&&- \cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
&=&- \left( \frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)^{2}\cos\theta
\end{aligned}
\end{equation}
$$

Finally, we have:
$$
\begin{equation}
{\overline{\overline{\mathbf{R}}}}^{- 1} = \frac{C_{1}}{{\cos\theta\left( \frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)}^{2}}\begin{bmatrix} 
  {- cos}\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \mathbf{-}\cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\
  \mathbf{-}\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}
  \end{bmatrix}.
  \end{equation}
$$

Note that the constant $C_{1}$ can be assumed equal to 1, yielding:

$$
\begin{equation}{\overline{\overline{\mathbf{R}}}}^{- 1} = \frac{1}{{\cos\theta\left( \frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \right)}^{2}}\begin{bmatrix} 
  {- cos}\theta\sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \mathbf{-}\cos\theta\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} \\   
  \mathbf{-}\cos\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y} & \sin\phi\frac{\cos X}{X^{2} - \left( \frac{\pi}{2} \right)^{2}}\frac{\sin Y}{Y}
  \end{bmatrix}.
  \end{equation}
$$

We can now use this matrix to correct the measured results in Eq. (6).
It is worth noting that for an observation point at $(\theta,\phi)$ in
the far field, in (18), we should use $- \phi$ to derive the corrections
coefficients.

## References:
<a id="1">[1]</a>
A. Yaghjian, "An overview of near-field antenna measurements,"
IEEE Transactions on Antennas and Propagation, vol. 34, no. 1, pp.
30-45, January 1986.

<a id="2">[2]</a> 
J. Appel-Hansen, "Antenna measurements," The Handbook of Antenna
Design, vol. 1. London: Peregrinus, cb. 8, 1982.

<a id="3">[3]</a> 
Balanis, C. A. (2016). Antenna Theory: Analysis and Design (4th
ed.). John Wiley & Sons.
