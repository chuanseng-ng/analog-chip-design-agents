* ngspice smoke test — resistive divider (PDK-independent)
* Exercises the real open-source tool path through wrap-ngspice.sh without
* depending on any PDK. A 1.0 V source across two equal 1k resistors gives
* v(mid) = 0.5 V, which wrap-ngspice.sh captures as the measure "vmid".
V1 in 0 DC 1.0
R1 in mid 1k
R2 mid 0 1k
.control
op
let vmid = v(mid)
print vmid
.endc
.end
