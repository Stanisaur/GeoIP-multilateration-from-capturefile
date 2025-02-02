# GeoIP-multilateration-from-capturefile
The aim of this repository is to allow for the geolocation of a host that has recorded a given wireshark capture file, ideally to a ~100km radius. Work in progress
adaptation of the Spotter 2011 paper:
> [**Spotter: A model based active geolocation service**]([https://doi.org/10.1109/INFCOM.2011.5935165](https://doi.org/10.1109/INFCOM.2011.5935165))  
> Laki, Sándor and Mátray, Péter and Hága, Péter and Sebők, Tamás and Csabai, István and Vattay, Gábor <br>
> *2011 Proceedings IEEE INFOCOM*
Using delay-distance relationship data from analysis at [https://github.com/Stanisaur/DistanceToRTTMapping](https://github.com/Stanisaur/DistanceToRTTMapping)

## Overview
Roughly speaking, each IP address that has been communicated with over TCP has info on the Round Trip Time (RTT). Using this we can draw a "ring" around the geolocated IP address. Do this for multiple IP addresses, and take the intersections with highest probability, and you have potential locations of the original capture. For example, say we have 3 data points from 3 addresses in the form [lat,long,RTT]:
```
[
(55.5, 4.5, 10.0)
(55.5, 1.5, 10.0)  
(51.1, 1.5, 10.0)
]
```
This, when fed into our main script, produces the following output:
![image](https://github.com/user-attachments/assets/b07fb2ec-3971-4dd3-9e05-40c2c00fcdad)
The more entries that are given, the better the guess becomes(as long as those entries are reliable).
## Requirements
- Conda
- Wireshark (or other packet analysis software) pcapng file with maxmind geodata included in the capturefile.

## Usage
From testing, this technique is only better than the simple method of taking the IP geolocation with lowest tcp Round Trip Time (RTT) in the scenario that you have >40ms RTT readings spread out in terms of location. All RTT's greater than 80ms are ignored as data becomes too fuzzy at that point
## Limitations
This project is a work in progress due to a few limitations that need to be worked around:
- the source for locations of IP's is MaxMind database files. These can be very inaccurate in terms of exact location and can become quickly outdated(new files are released every month). For example, the IP address 18.165.160.88 is claimed to be a US based IP address(you can check this [here](https://nordvpn.com/ip-lookup/)), however when I ping it from Glasgow, Scotland in my UNIX terminal using the command:
```
ping 18.165.160.88
```
I get latencies of <20ms which is simply not possible. This is very hard to deal with, will have to use a form of [RANSAC](https://en.wikipedia.org/wiki/Random_sample_consensus) to try to negate this.
