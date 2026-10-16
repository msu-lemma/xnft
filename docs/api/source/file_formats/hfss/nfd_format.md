Ansys HFSS Near-field File Format
====================

The Ansys HFSS near-field data format is labeled `.nfd` and contains the near-field E- and H-field data as a function of x, y, z, and frequency.  

File Example
------------
A header is included in this file to indicate quantities.
```txt
#Index, X, Y, Z, Ex(real, imag), Ey(real, imag), Ez(real, imag), Hx(real, imag), Hy(real, imag), Hz(real, imag)
Frequencies 1
Frequency 5.800000e+09
1, -2.500000e-02, -2.500000e-02, 0.000000e+00, 3.229143e+01, 2.033957e+01, -5.859852e+01, 5.286398e+00, -7.310121e+01, -8.673565e+01, 1.055174e-01, 2.632093e-01, -1.987995e-01, -2.025219e-02, 1.952461e-01, 1.231731e-04
2, -2.500000e-02, -2.450000e-02, 0.000000e+00, 3.194806e+01, 2.220217e+01, -6.017212e+01, 1.855963e+00, -6.954680e+01, -8.999728e+01, 9.174575e-02, 2.710272e-01, -2.005923e-01, -2.741153e-02, 2.007037e-01, 8.692162e-03
3, -2.500000e-02, -2.400000e-02, 0.000000e+00, 3.153842e+01, 2.399355e+01, -6.171521e+01, -1.703009e+00, -6.593898e+01, -9.302685e+01, 7.764453e-02, 2.780580e-01, -2.021042e-01, -3.461753e-02, 2.062565e-01, 1.755524e-02
4, -2.500000e-02, -2.350000e-02, 0.000000e+00, 3.104705e+01, 2.585402e+01, -6.310243e+01, -5.435405e+00, -6.221044e+01, -9.583359e+01, 6.303770e-02, 2.845374e-01, -2.035426e-01, -4.169355e-02, 2.115770e-01, 2.687424e-02
5, -2.500000e-02, -2.300000e-02, 0.000000e+00, 3.046655e+01, 2.770344e+01, -6.438179e+01, -9.313002e+00, -5.840044e+01, -9.838914e+01, 4.804652e-02, 2.903270e-01, -2.048053e-01, -4.864433e-02, 2.167915e-01, 3.655313e-02
6, -2.500000e-02, -2.250000e-02, 0.000000e+00, 2.978039e+01, 2.953904e+01, -6.554525e+01, -1.332919e+01, -5.452420e+01, -1.006805e+02, 3.263834e-02, 2.953697e-01, -2.059332e-01, -5.547410e-02, 2.218739e-01, 4.657086e-02
7, -2.500000e-02, -2.200000e-02, 0.000000e+00, 2.897184e+01, 3.135827e+01, -6.660329e+01, -1.746815e+01, -5.058051e+01, -1.026959e+02, 1.687485e-02, 2.995523e-01, -2.069313e-01, -6.213905e-02, 2.267496e-01, 5.696782e-02
8, -2.500000e-02, -2.150000e-02, 0.000000e+00, 2.805293e+01, 3.312880e+01, -6.751122e+01, -2.171285e+01, -4.658232e+01, -1.044517e+02, 6.419147e-04, 3.032142e-01, -2.078512e-01, -6.861600e-02, 2.315658e-01, 6.748876e-02
9, -2.500000e-02, -2.100000e-02, 0.000000e+00, 2.698839e+01, 3.489789e+01, -6.822224e+01, -2.608168e+01, -4.251306e+01, -1.059453e+02, -1.618086e-02, 3.061013e-01, -2.086474e-01, -7.488698e-02, 2.360198e-01, 7.840582e-02

...
```

Sample Locations
----------------
The file header begins with the near-field sample locations in cartesian coordinates in unit of meters. Unfortunately, the sample locations array is dimensions are not provided ahead of time and must be computed based on reading in the entire dataset.

Frequencies
-----------
File contains multiple frequencies the solve was performed at.  The total number of frequencies is listed in the file header, e.g.:
```
...
Frequencies 1
...
```
indicates a single solve frequency.

The body of the file then proceeds with the first solve frequency in Hertz, followed by the E-field data, e.g.:
```txt
...
Frequency 5.800000000000000e+09
1, -2.500000e-02, -2.500000e-02, 0.000000e+00, 3.229143e+01, 2.033957e+01, -5.859852e+01, 5.286398e+00, -7.310121e+01, -8.673565e+01, 1.055174e-01, 2.632093e-01, -1.987995e-01, -2.025219e-02, 1.952461e-01, 1.231731e-04
...
```
indicating a solve frequency of 5.8 GHz.

