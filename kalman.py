import numpy as np
import matplotlib as plt
import matplotlib.pyplot as plt
def kalman_filter( measurment,e_mea, prev_e_est, prev_estimate ):
    kalman_gain = prev_e_est/(prev_e_est+e_mea)
    print("Kalman gain =" + str(kalman_gain))
    estimate = prev_estimate + kalman_gain*(measurment - prev_estimate)
    print("New Estimate =" + str(estimate))
    e_est = (1.00-kalman_gain)*prev_e_est
    print("New estimate error =" + str(e_est))
    print("**** func end ****")
    val = (kalman_gain , estimate , e_est)
    return val

e_mea= float(input("please input the error of the sensing device"))
measurments = np.random.uniform(100, 200, size=100)
for i in range(2, 100):
    measurment = np.random.uniform(100+i*6, 200+ i*6, size=100)
    measurments = np.hstack((measurments,measurment))
print(measurments)
print(measurments.mean())
c = 0
iter =kalman_filter(measurments[0], e_mea, 100,0)
x= [float(iter[1])]
while c<len(measurments):
    measurment = measurments[c]
    iter = kalman_filter(measurment,e_mea,iter[2],iter[1])
    x.append(float(iter[1]))
    c+=1
print(x)
t = [0]
i=0
while i < len(x)-1:
    t.append(i)
    i+=1
plt.plot(t, x)
plt.plot(t, list(measurments)+[measurments[-1]])
plt.ylabel('estimates')
plt.xlabel('time')
plt.title('measurements')
plt.show()