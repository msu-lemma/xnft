Ansys HFSS Far-field File Format
====================

The Ansys HFSS far-field data format is labeled `.ffd` and contains the far-field E-field data as a function of azimuth, elevation, and frequency.  

File Example
------------
```txt
-180 180 181
-180 180 181
Frequencies 1
Frequency 5.800000000000000e+09
1.427873686152934e-02 -1.813977115533172e-02 1.057332503981753e+00 -6.736426815104894e-01
-2.263033359532683e-02 5.381069645175263e-03 1.057186726318509e+00 -6.738653854737470e-01
-5.951183247663273e-02 2.889535444120968e-02 1.055752929476377e+00 -6.732670882658097e-01
-9.632082535716113e-02 5.237443469884609e-02 1.053032860315951e+00 -6.718485188196653e-01
...
```

Sample Locations
----------------
The file header begins with the far field sample locations in unit degrees.  The format is
```
<theta_min> <theta_max> <theta_num_points>  # elevation
<phi_min> <phi_max> <phi_num_points>        # azimuth
...
```

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
1.427873686152934e-02 -1.813977115533172e-02 1.057332503981753e+00 -6.736426815104894e-01
...
```
indicating a solve frequency of 5.8 GHz.

Field Data
----------
The field data contained is the E-field far-field measurements as a complex value. The column format is:
```txt
<rEphi.real> <rEphi.imag> <rEtheta.real> <rEtheta.imag>
```
Each row of the matrix first iterates over the elevation (theta), then azimuth (phi).  An example mapping of the row number to phi and theta for the above file snippet is:

```txt
row #   theta    phi
----------------------
0       -180    -180
1       -179    -180
2       -178    -180
...
32760    179     180
32761    180     180
```