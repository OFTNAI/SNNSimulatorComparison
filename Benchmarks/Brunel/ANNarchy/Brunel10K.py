import getopt, sys, timeit
try:
    optlist, args = getopt.getopt(sys.argv[1:], '', ['plastic', 'fast', 'simtime='])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(2)

simtime = 1.0
fast = False
plastic = False
for o, a in optlist:
    if (o == "--fast"):
        fast = True
        print("Running without Monitoring Spikes (fast mode)\n")
    elif (o == "--simtime"):
        simtime=float(a)
        print("Simulation Time: " + a)
    elif (o == "--plastic"):
        plastic = True
        print("Running with plasticity on\n")

from ANNarchy import *
from pylab import *
from scipy.io import mmread

# ###########################################
# Configuration
# ###########################################
timestep_val = 0.1
setup(dt=timestep_val)
record = False
plot_all = False
if (not fast):
    record = True
    plot_all = True

# ###########################################
# Parameters
# ###########################################
g       = 5.0    # Ratio of IPSP to EPSP amplitude: J_I/J_E
delay   = 1.5    # synaptic delay in ms
V_th    = 20.0   # Spike threshold in mV
Nrec    = 1000     # Number of neurons to record 

NE = 8000
NI = 2000
N  = NE+NI
CE = int(NE/10) # number of excitatory synapses per neuron
CI = int(NI/10) # number of inhibitory synapses per neuron
JE = 0.1
JI = -g*JE

# ###########################################
# Neuron model
# ###########################################
IAF = Neuron(
    parameters="""
        v_th = 20.0 : population
        tau_m = 20.0 : population
    """,
    equations="""
        # The real equation should be:
        # tau_m * dv/dt = -v + g_exc + g_inh
        # But incoming spikes increment the membrane potential directly
        # So we apply the numerical method by hand
        v += g_exc + g_inh - dt*v/tau_m
    """,
    spike="v > v_th",
    reset="v = 0.0",
    refractory=2.0
)

# ###########################################
# Synapse model
# ###########################################
STDP = Synapse(
    parameters="""
        tau_stdp = 20.0 : postsynaptic
        wmax = 0.3 : postsynaptic
        lbda = 0.01 : postsynaptic
        alpha = 2.02 : postsynaptic
    """,
    equations = """
        tau_stdp * dApre/dt = -Apre : event-driven
        tau_stdp * dApost/dt = -Apost : event-driven
    """,
    pre_spike="""
        Apre += 1.0
        w -= lbda * alpha * w * Apost : min=0.0
    """,                  
    post_spike="""
        Apost += 1.0
        w += lbda * (wmax - w) * Apre : max=wmax 
    """
)

# ###########################################
# Populations
# ###########################################
P = Population(geometry=N, neuron=IAF)
PE= P[:NE]
PI= P[NE:]
P.v = 0.0#Uniform(-V_th, 0.95*V_th)

noise = PoissonPopulation(geometry=10000, rates=20.0)

# ###########################################
# Projections
# ###########################################
A = mmread('../ee.wmat')
A = A.tolil()
A[A != 0.0] = JE
if (plastic):
    ee = Projection(PE, PE, 'exc', STDP)
else:
    ee = Projection(pre=PE, post=PE, target='exc')
ee.connect_from_sparse(A.tocsr()) #weights=0.4*gleak, delays=delayval)

A = mmread('../ei.wmat')
A = A.tolil()
A[A != 0.0] = JE
ei = Projection(pre=PE, post=PI, target='exc')
ei.connect_from_sparse(A.tocsr()) #weights=0.4*gleak, delays=delayval)


A = mmread('../ie.wmat')
A = A.tolil()
A[A != 0.0] = JI
ie = Projection(pre=PI, post=PE, target='inh')
ie.connect_from_sparse(A.tocsr()) #weights=0.4*gleak, delays=delayval)

A = mmread('../ii.wmat')
A = A.tolil()
A[A != 0.0] = JI
ii = Projection(pre=PI, post=PI, target='inh')
ii.connect_from_sparse(A.tocsr()) #weights=0.4*gleak, delays=delayval)

noisy = Projection(noise, P, 'exc')
noisy.connect_fixed_number_pre(number=1000, weights=JE, delays=delay)

'''
ee = []
if (plastic):
    ee = Projection(PE, PE, 'exc', STDP)
else:
    ee = Projection(PE, PE, 'exc')
ee.connect_fixed_number_pre(number=CE, weights=JE, delays=delay)
ei = Projection(PE, PI, 'exc')
ei.connect_fixed_number_pre(number=CE, weights=JE, delays=delay)
ii = Projection(PI, P , 'inh')
ii.connect_fixed_number_pre(number=CI, weights=JI, delays=delay)
noisy = Projection(noise, P, 'exc')
noisy.connect_fixed_number_pre(number=1000, weights=JE, delays=delay)
'''

compile()

# ###########################################
# Simulation
# ###########################################
print 'Start simulation'
if record :
    m = Monitor(P[:Nrec], 'spike')


if (fast):
    starttime = time.clock()

simulate(simtime*1000.0, measure_time=True)

if (fast):
    totaltime = time.clock() - starttime
    f = open("timefile.dat", "w")
    f.write("%f" % totaltime)
    f.close()

# ###########################################
# Data analysis
# ###########################################
if record:
    data = m.get()
    t, n = m.raster_plot(data['spike'])
    print 'Mean firing rate:', len(t)/(float(Nrec)*simtime), 'Hz'
    weights = ee.w
    flat_weights = [item for sublist in weights for item in sublist]
    np.savetxt("plasticweights.txt", np.asarray(flat_weights))


