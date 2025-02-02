import pyshark
from scipy.stats import norm
import numpy as np
from numpy.polynomial import Polynomial as P
from haversine import haversine_vector, Unit
import folium
from folium.plugins import HeatMap

#predefined coefficients, see https://github.com/Stanisaur/DistanceToRTTMapping for details
mu_coefficients = np.array([0,49.6080905, -0.237745386, -0.00328554308, 0.0000551577256])
si_coefficients = np.array([0,17.2876406, -0.589392994, 0.0105034666, -0.0000441354642])

mu = P(mu_coefficients)
si = P(si_coefficients)

output = {}
cap = pyshark.FileCapture('test4.pcapng', display_filter="ip.geoip.lon and tcp.analysis.initial_rtt")
for packet in cap:
    rtt = np.float64(packet.tcp.analysis_initial_rtt) * 800
    if packet.ip.src in output:
        output[packet.ip.src]["iRTT"] = min(rtt, output[packet.ip.src]["iRTT"])
    else:
        output[packet.ip.src] = {}
        output[packet.ip.src]["iRTT"] = rtt
        output[packet.ip.src]["long"] = np.float64(packet.ip.geolon)
        output[packet.ip.src]["lat"] = np.float64(packet.ip.geolat)

    if packet.ip.dst in output:
        output[packet.ip.dst]["iRTT"] = min(rtt, output[packet.ip.dst]["iRTT"])
    else:
        output[packet.ip.dst] = {}
        output[packet.ip.dst]["iRTT"] = rtt
        output[packet.ip.dst]["long"] = np.float64(packet.ip.geolon)
        output[packet.ip.dst]["lat"] = np.float64(packet.ip.geolat)

#this output will have local address also, mistakenly given coordinates, so we just make new dict that filters out 
#duplicate locations
seen = set()
output = {key:output[key] for key in output if not (output[key]['long'] in seen or seen.add(output[key]['lat']))}


def f_d(delay):
    d = np.float64(delay)
    return norm(loc=mu(d), scale=si(d)).logpdf

#step one: for every ip, use the RTT to get a function and save it to da ip address
for key in output:
    output[key]["pdf"] = f_d(output[key]["iRTT"])

# Define the geographic bounds (adjust as needed)
lon_min, lon_max = -180, 180
lat_min, lat_max = -90, 90
resolution = 0.01  # Degrees per grid point
# Create grid points
lons = np.arange(lon_min, lon_max, 0.1)
lats = np.arange(lat_min, lat_max, 0.1)
lon_grid, lat_grid = np.meshgrid(lons, lats)

coordinates = np.column_stack((lat_grid.ravel(),lon_grid.ravel()))
final_probs = np.zeros(coordinates.shape[0])
i = 0
for key, value in sorted(output.items(), key=lambda x: x[1]['iRTT']):
    distances = haversine_vector(np.tile([output[key]["lat"],output[key]["long"]], (len(coordinates), 1)),
                                    coordinates, unit= Unit.KILOMETERS)
    final_probs += output[key]["pdf"](distances)
    i+=1
    if i > 10:
        break

final_probs = np.exp(final_probs -np.max(final_probs))
results = np.column_stack((coordinates, final_probs))
results = results[results[:, 2] > np.percentile(results[:, 2], 99.5)] 

map_object = folium.Map()
HeatMap(results).add_to(map_object)
map_object.save("index.html")

