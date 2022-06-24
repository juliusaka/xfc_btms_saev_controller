# MPC Base

## three level approach

1. Level: economical optimization (sizing) of BTMS-size
    - for unconstrained case, i.e. all cars are charged immediatly.
    - Can apply before level 2 a factor to decrease the BTMS size, as this size should be seen as an upper limit, where charging of vehicle isn't decreased.
2. Level: optimal long-term/day-ahead plan for charging
3. Level: real-time trajectory following MPC algorithm

## 1. Level: Economical Optimization of BTMS-Size

in *determineBtmsSize()*:

$$\begin{equation}
\min \quad a \cdot (P_{slack} - P_{free}) + b \cdot \Sigma_{k=0}^{T} P_{BTMS,Ch}(k)dt + c \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt)
\end{equation}$$
subject to:
$$\begin{align}
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k)) \quad &\forall k \in [0,T]\\
P_{Charge}(k) &= P_{Grid}(k) - P_{BTMS}(k) \quad &\forall k \in [0,T]  \\
P_{BTMS}(k) &= P_{BTMS,Ch}(k) + P_{BTMS,DCh}(k) \quad &\forall k \in [0,T]\\
P_{BTMS,Ch}(k) &\geq 0 \quad &\forall k \in [0,T]\\
P_{BTMS,DCh}(k) &\leq 0 \quad &\forall k \in [0,T]\\
E_{BTMS}(0) &= E_{BTMS}(T+1)\\
E_{BTMS}(0) &= 0\\
P_{slack} &\geq \max(P_{Grid}(k))\\
P_{slack} &\geq P_{free}
\end{align}$$

where $a$ is the demand charge per day, $b$ is the BTMS cost per cycle per kWh and c is the electricity cost. $P_{Grid}$ is the power withdrawal from the electric grid, $P_{BTMS}$ is the power to/from the behind the meter storage and $P_{Charge}$ is the unconstrained power flow of the charging station, which is determined in the class-method *generatePredictions()*, with a simple algorithm, considering vehicle arrivals and the maximum number of available charging bays at the charging station. $E_{BTMS}$ is the energy content of the behind the meter storage, and its size is left open to be determined by the optimization. Under the assumption of a periodic behaviour over each day, we set  the constraint $ E_{BTMS}(0) = E_{BTMS}(T+1) $ to avoid the optimization of just discharging the BTMS to reduce cost. To correctly implement charging losses, we assume that the same charging loss occurs while charging and discharge, and model these effects with two variables $P_{BTMS,Ch}$ and $P_{BTMS,DCh}$, please see remark at bottom for a further explanation of this.

The objective is to minimize the sum of demand charge, the usage cost of the BTMS as the cost of storing/releasing energy in terms of cycles and the energy loss cost. As demand charges can be applied after exceeding a certain level, we choosed a formulation which returns the exceeding of a certain power level $P_{free}$. The term $P_{slack} - P_{free}$ is 0 as long as $\max(P_{Grid}) \leq P_{free}$, and gives after that the difference to the free power level.

As the problem is convex in objective function and constraints, a solution can be efficiently determined with open-source accessible solvers. We use the mathematical modeling language *cvxpy*. For the implementation, we defined the following states, control and disturbance(input) variables. We also define the slack variable for a free power level before demand charge:
$\begin{align}
x(k) &= [E_{BTMS}(k)] \\
u(k) &= [P_{Grid}(k), P_{BTMS}(k), P_{BTMS,Ch}(k), P_{BTMS,DCh}(k)] \\
i(k) &= [P_{Charge}(k)]\\
P_{slack}
\end{align}$

With this formulization, the BTMS-size is determined as $\max(E_{BTMS}) - \min(E_{BTMS})$. The maximum power delivery of the BTMS is unconstrained and can therefore reach high C-Ratings, especially when you choose high BTMS cycle cost compared to demand charges. Integrating a C-Rating into this optimization problem leads to a non-convex formulization which would have to be solved with a less efficient solver and isn't guarenteed to be globally optimal. As we try to assess future scenarios, higher C-ratings are probably possible, so that this shouldn't be off to much concern for us.

After determining the BTMS-size for unconstrained charging, it is possible to reduce the size to e.g. assess the impact of this on SAEV-fleets.

**option**: We might add a constraint to implement a maximal C-Rating of the BTMS. Need to investigate if problem is still convex then.

### correct implementation of charging losses

You might assume that the equation for the dynamics of the energy content is
$\begin{equation}
E_{BTMS}(k+1) = E(k) + dt \cdot \eta \cdot P_{BTMS}(k)
\end{equation}$
when charging for k=0 and discharging for k=1, and assuming that the energy level should be the same after this operation ($E_{BTMS}(0) = E_{BTMS}(2)$), we get
$\begin{align}
E_{BTMS}(1) &= E(0) + dt \cdot \eta \cdot P_{BTMS}(0)\\
E_{BTMS}(2) &= E(1) + dt \cdot \eta \cdot P_{BTMS}(1) \quad | E_{BTMS}(0) = E_{BTMS}(2)\\
P_{BTMS}(1) &= - P_{BTMS}(0)
\end{align}$
Where the in- and outflowing powers within one timestep are the same, which means no physical energy loss occured. This is because the effect of $\eta$ cancels out with the choosen formulation.

Rewriting the energy equation with constraints as
$\begin{align}
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k))\\
P_{BTMS,Ch}(k) &\geq 0 \\
P_{BTMS,DCh}(k) &\leq 0 \\
\end{align}$

delivers for the same cycle
$\begin{equation}
P_{BTMS,DCh}(1) = -\eta^2 P_{BTMS,Ch}(0)
\end{equation}$
which represents the energy loss correctly. Likewise, we are also able to implement the cost of the energy los as ($P_{BTMS,DCh} \leq 0$)
$\begin{equation}
C_{loss} = c_{el} \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt)
\end{equation}$
with $c_{el}$ as the electricity cost. This is only valid when assuming $E_{BTMS}(k=0) = E_{BTMS}(k=T+1)$.

## 2. Level: Optimal day-ahead/long-term plan

in *planning()*:

$\begin{equation}
\begin{aligned}
\min \quad a \cdot (P_{slack} - P_{free}) + b \cdot \Sigma_{k=0}^{T} P_{BTMS,Ch}(k)dt + c \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt) \\\
+\Sigma_{k=0}^{k=T+1} d(k) \cdot t_{wait}(k)
\end{aligned}
\end{equation}$

subject to:
$\begin{align}
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k)) \quad &\forall k \in [0,T]\\
E_{Shift}(k+1) &= E_{Shift}(k) + dt \cdot P_{Shift}(k) \\
P_{Charge}(k) - P_{Shift}(k) &= P_{Grid}(k) - P_{BTMS}(k) \quad &\forall k \in [0,T]  \\
P_{BTMS}(k) &= P_{BTMS,Ch}(k) + P_{BTMS,DCh}(k) \quad &\forall k \in [0,T]\\
P_{BTMS,Ch}(k) &\geq 0 \quad &\forall k \in [0,T]\\
P_{BTMS,DCh}(k) &\leq 0 \quad &\forall k \in [0,T]\\
t_{wait}(k) &\geq dt \cdot (n_a(k) +n_b(k)) &\forall k \in [0,T] \\
n_a(k) &\geq \frac{E_{Shift}(k)}{P_{ch,avg} \cdot dt} &\forall k \in [0,T] \\
n_b(k) &\geq \frac{P_{Shift}(k)}{P_{ch,avg}} &\forall k \in [0,T] \\
n_b(k) &\geq 0 &\forall k \in [0,T]\\
E_{BTMS}(k) &\geq 0 \quad &\forall k \in [0,T+1]\\
E_{BTMS}(k) &\leq \Delta E_{BTMS} \quad &\forall k \in [0,T+1] \\
E_{Shift}(k) &\geq 0 \quad &\forall k \in [0,T+1]\\
E_{BTMS}(0) &= E_{BTMS}(T+1)\\
E_{Shift}(0) &= 0\\
P_{slack} &\geq \max(P_{Grid}(k))\\
P_{slack} &\geq P_{free}\\
\end{align}$
We added the BTMS size $\Delta E_{BTMS}$ to the constraint, and ensured that the energy level is between this and 0. Furthermore, we set $E_{BTMS}(0) = E_{BTMS}(T+1)$ to ensure that the BTMS isn't completly discharged in our case of a one day simulation. For real-world usage, optimization for 2 or 3 days in advance might be better solution, with just using the results for the first day.

Compared to the approach described in 1st level for determining BTMS-size, we added the ability to shift charging power, i.e. to decrease charging speed of vehicles. For this, we increase the state of shifted energy $E_{Shift}$ which serves as a stock for the shifted power and has an equal defintion of the earlier introduced energy lag. We then derive from the shifted energy the generated waiting time $t_{wait}$, which can be penalized with the tuning parameter $d(k)$. This parameter $d(k)$ is defined for every timestep, so that e.g. higher waiting time cost at ride-hailing peak-demand times could be implemented, to further prioritize having enough available charging power at these times. Please look down in the document to understand, how we dervie the waiting time.

We define our state, control, disturbance and slack variables as:
$\begin{align}
x(k) &= [E_{BTMS}(k), E_{Shift}(k)]\\
u(k) &= [P_{Grid}(k), P_{BTMS}(k), P_{BTMS,Ch}(k), P_{BTMS,DCh}(k), P_{Shift}(k)] \\
i(k) &= [P_{Charge}(k)]\\
P_{slack}(k), & t_{wait}(k), n(k) = [n_a(k), n_b(k)]
\end{align}$

From this, we can obtain a trajectory for the desired Energy Level in the behind the meter storage. From this, we determine a load band with $\beta$ upper and lower deviations of the BTMS-size $\Delta E_{BTMS}$. We apply the min- and max-function to ensure, that we don't exceed storage size with this.

$\begin{align}
E_{BTMS,lower}(k) &= \max([0\text{kWh}, E_{BTMS}(k)-\beta\Delta E_{BTMS}])\\
E_{BTMS,upper}(k) &= \min([\Delta E_{BTMS}, E_{BTMS}(k)+\beta\Delta E_{BTMS}])
\end{align}$

**remark 1**: We might have to add a constraint to ensure that the shifted energy does match 0 at the end, but ideally, the cost function should do this (e.g. $E_{Shift}(T) = 0$).

**remark 2**: In order to correctly weigh the parameters of the cost-function to each other, we assume that we optimize over one day. For that, we divide the demand charge in such a way, that it is projected to one day. e.g. if it is given for one month, we divide it by 30 days. 

**remark 3**: The code also allows to add a C-Rating, which adds the constraint
$\begin{align}
P_{BTMS,Ch}(k) &\leq C \cdot \Delta E_{BTMS} \quad &\forall k \in [0,T]\\
P_{BTMS,DCh}(k) &\geq C \cdot \Delta E_{BTMS} \quad &\forall k \in [0,T]\\
\end{align}$

**Option**: We could also include predictions for power grid constraints like
$$\begin{equation*}
P_{Grid}(k) \leq P_{Grid,Limit,pred}(k) \quad \forall k \in [0,T]
\end{equation*}$$

### explanation of waiting time

The waiting at the charging station is the result of 2 values:

- a) waiting time due to already shifted energy at time $k$
- b) waiting time due to shifted energy at time $k$

<img src="informations/04_18_22 MPC types.png" alt="explanation of waiting time" style="height: 400px;"/>

For a), the number of vehicles which is resembled by the already shifted energy $E_{Shift}$ can be calculated as:
$\begin{equation}
n_a(k) = \frac{E_{Shift}(k)}{P_{ch,avg} \cdot dt}
\end{equation}$ 

For b), the number of vehicles which is resembled by the newly shifted energy $P_{Shift}\cdot dt$ can be calculated as
$\begin{equation}
n_b(k) = \frac{P_{Shift}(k)\cdot dt}{P_{ch,avg}\cdot dt}
\end{equation}$ 
which is valid for the case $P_{Shift}(k)\geq0$. If $P_{Shift}(k)<0$, the vehicles are released at the end of the timestep, so that they are within the timestep still at the charging station, which means we have to add a constraint that $n_b(k) \geq 0$.

The total waiting time increase during one time step is then the number of waiting vehicles multiplied by the duration of one timestep
$\begin{equation}
t_{wait}(k) = dt \cdot (n_a(k) +n_b(k))
\end{equation}$ 

To express this as constraints of the minimization problem, we write

$\begin{align}
t_{wait}(k) &\geq dt \cdot (n_a(k) +n_b(k))\\
n_a(k) &\geq \frac{E_{Shift}(k)}{P_{ch,avg} \cdot dt} \\
n_b(k) &\geq \frac{P_{Shift}(k)\cdot dt}{P_{ch,avg}\cdot dt}\\
n_b(k) &\geq 0
\end{align}$

**draft result**: It seems like the economical value of waiting time is higher opposed to demand charges and btms cost. For example, for a waiting time cost of 1$/hour, a demand charge of 20$/kW, a BTMS cost of 200$/kWh for 5000 cycles, and an electricity price of 0.15$/kWh with an BTMS efficiency of 90%, no waiting time is considered to reduce the other factors. Only for BTMS prices of over 500$/kWh for 5000 cycles, small amounts of waiting times are considered. This preliminary result should be cross checked with more BEAM-simulation results and correct infrastructure settings, but the preliminary results show that waiting time are probably economical to avoid.

## 3. Level: short horizoned model predictive control

based on the preliminary finding from the previous controller, we don't design a MPC with a sophisticated wait time integration, i.e. we will just introduce one slack variable to maintain a feasible solution for all cases, if power demand of charging can't be satisfied with avaialble grid and charging power resources. This is only necessary for the stand-alone version.

In order to align with the goal to show how control can benefit on keeping the stress low for the electric grid, we choose the objective to be a minimization of deviations of the grid power from the average.

in *step()*:
$\begin{equation}
\begin{aligned}
\min \quad \Sigma_{k=-1}^{N} (P_{Grid}(k) - P_{avg}(k)) + \Sigma_{k=0}^{N} M_1 t_1(k) + M_2 t_2(k)
\end{aligned}
\end{equation}$

Here, $N$ is the prediction horizon of the short horizoned MPC, $M_1$ and $M_2$ are big numbers and $t_1$ and $t_2$ are slack variables to maintain feasibility for infeasible combinations of variable sets. We also include the last power withdrawal $P_{Grid}(k=-1)$ from the grid to avoid big jumps.

subject to:
$\begin{align}
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k)) \quad &\forall k \in [0,N]\\
E_{V}(k+1) &= E_{V}(k) + dt \cdot P_{Charge}(k) \quad &\forall k \in [0,N]\\
P_{Charge}(k) &= P_{Grid}(k) - P_{BTMS}(k) \quad &\forall k \in [0,N]  \\
P_{BTMS}(k) &= P_{BTMS,Ch}(k) + P_{BTMS,DCh}(k) \quad &\forall k \in [0,N]\\
P_{Grid}(k) &\leq \max (P_{Grid,planning}(i)) + t_2(k) \quad &\forall k \in [0,N]\\
P_{Grid}(k) &\leq P_{Grid,DERMS} \quad &\forall k \in [0,N]\\
P_{BTMS,Ch}(k) &\geq 0 \quad &\forall k \in [0,N]\\
P_{BTMS,DCh}(k) &\leq 0 \quad &\forall k \in [0,N]\\
P_{Charge}(k) &\geq 0 \quad &\forall k \in [0,N]\\
E_{BTMS}(k) &\geq 0 \quad &\forall k \in [0,N+1]\\
E_{BTMS}(k) &\leq \Delta E_{BTMS} \quad &\forall k \in [0,N+1] \\
E_{BTMS}(k) &\geq E_{BTMS,lower}(k) \quad &\forall k \in [1,N+1]\\
E_{BTMS}(k) &\leq E_{BTMS,lower}(k) \quad &\forall k \in [1,N+1]\\
E_{V}(k) &\geq E_{V,lower}(k) - t_1(k) \quad &\forall k \in [1,N+1]\\
E_{V}(k) &\leq E_{V,upper}(k) \quad &\forall k \in [1,N+1]\\
E_{BTMS}(0) &= E_{BTMS,PhySim}\\
E_{V}(0) &= 0 \\
\end{align}$

Compared to the fomulations before, $P_{Charge}(k)$ is now a variable determined to satisfy the charging demand for Vehicles $E_{V,lower}(k)$ and $E_{V,upper}(k)$, which are determined as the sum of the vehicle object function *determineChargingTrajectory()*. The function returns an upper and lower bound for the necessary energy transfered to each vehicle. The lower bound is a trajectory which need to be fullfilled to reach the desired end in time, the upper bound is a trajectory which resemble the fastet possible charge. The time in between is allowed flexibility. Likewise, we added a differntial equaiton for the aggregated energy level in the vehicles $E_{V}(k)$.  
We added the slack variable $t_1$ to the minimal needed energy to maintain feasibility for all cases, i.e. by delaying the charge of a vehicle. Feasibility can also by maintained by exceeding the power limit $\max (P_{Grid,planning}(i))$ from planning, which is penalized by the slack variable $t_2$. By weighing the values of $M_1$ and $M_2$ against each other, one of both feasiblity sustaining methods can be favoured.  
The charging power $P_{Charge}(k)$ should be distributed by the charging desire of each vehicle. (sharing power doesn't make sense to reduce average waiting times, see this one paper)

We initialize each run of the short horizoned MPC with the energy level of the BTMS, which will be given from the physical simulation.

To summarize the variables, we have:
$\begin{align}
x(k) &= [E_{BTMS}(k), E_{V}(k)]\\
u(k) &= [P_{Grid}(k), P_{BTMS}(k), P_{BTMS,Ch}(k), P_{BTMS,DCh}(k), P_{Charge}(k)] \\
t_1, t_2
\end{align}$
inputs to our algortihm are
$\begin{align}
&P_{Grid}(k=-1), \max({P_{Grid,planning(i)}}), P_{Grid,DERMS}, \Delta E_{BTMS},\\ 
&E_{BTMS,lower}(k), E_{BTMS,upper}(k), E_{V,lower}(k), E_{V,upper}(k), E_{BTMS,PhySim}
\end{align}$