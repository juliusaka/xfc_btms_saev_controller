# MPC Base

## three level approach

1. Level: economical optimization of BTMS-size
    - for unconstrained case, i.e. all cars are charged immediatly. 
    - Can apply before level 2 a factor to decrease the BTMS size, as this size should be seen as an upper limit, where charging of vehicle isn't decreased.
2. Level: optimal long-term/day-ahead plan for charging
3. Level: real-time trajectory following MPC algorithm

## 1. Level: Economical Optimization of BTMS-Size
in *determineBtmsSize()*:

$\begin{equation} 
\min \quad a \cdot (P_{slack} - P_{free}) + b \cdot \Sigma_{k=0}^{T} P_{BTMS,Ch}(k)dt + c \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt)
\end{equation}$
subject to:
$\begin{align} 
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k)) \quad &\forall k \in [0,T]\\ 
P_{Charge}(k) &= P_{Grid}(k) - P_{BTMS}(k) \quad &\forall k \in [0,T]  \\
P_{BTMS}(k) &= P_{BTMS,Ch}(k) + P_{BTMS,DCh}(k) \quad &\forall k \in [0,T]\\
P_{BTMS,Ch}(k) &\geq 0 \quad &\forall k \in [0,T]\\
P_{BTMS,DCh}(k) &\leq 0 \quad &\forall k \in [0,T]\\
E_{BTMS}(0) &= E_{BTMS}(T+1)\\
E_{BTMS}(0) &= 0\\
P_{slack} &\geq \max(P_{Grid}(k))\\
P_{slack} &\geq P_{free}
\end{align}$

where $a$ is the demand charge per day, $b$ is the BTMS cost per cycle and c is the electricity cost. $P_{Grid}$ is the power withdrawal from the electric grid, $P_{BTMS}$ is the power to/from the behind the meter storage and $P_{Charge}$ is the unconstrained power flow of the charging station, which is determined in the class-method *generatePredictions()*, with a simple algorithm, considering vehicle arrivals and the maximum number of available charging bays at the charging station. $E_{BTMS}$ is the energy content of the behind the meter storage, and its size is left open to be determined by the optimization. To correctly implement charging losses, we assume that the same charging loss occurs while charging and discharge, and model these effects with two variables $P_{BTMS,Ch}$ and $P_{BTMS,DCh}$, please see remark at bottom for a proof of this.

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

### correct implementation of charging losses
You could assume that the equation for the dynamics of the energy content is
$\begin{equation*}
E_{BTMS}(k+1) = E(k) + dt \cdot \eta \cdot P_{BTMS}(k)
\end{equation*}$
when charging for k=0 and discharging for k=1, and assuming that the energy level should be the same after this operation ($E_{BTMS}(0) = E_{BTMS}(2)$), we get
$\begin{align*}
E_{BTMS}(1) &= E(0) + dt \cdot \eta \cdot P_{BTMS}(0)\\
E_{BTMS}(2) &= E(1) + dt \cdot \eta \cdot P_{BTMS}(1) \quad | E_{BTMS}(0) = E_{BTMS}(2)\\
P_{BTMS}(1) &= - P_{BTMS}(0)
\end{align*}$
Where the in- and outflowing powers within one timestep are the same, which means no physical energy loss occured. This is because the effect of $\eta$ cancels out with the choosen formulation.

Rewriting the equation with constraints as
$\begin{align*}
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot (\eta \cdot P_{BTMS,Ch}(k) + \frac{1}{\eta}P_{BTMS,DCh}(k))\\
P_{BTMS,Ch}(k) &\geq 0 \\
P_{BTMS,DCh}(k) &\leq 0 \\
\end{align*}$

delivers for the same cycle
$\begin{equation*}
P_{BTMS,DCh}(1) = -\eta^2 P_{BTMS,Ch}(0)
\end{equation*}$
which represents the energy loss correctly. Likewise, we are also able to implement the cost of the energy los as ($P_{BTMS,DCh} \leq 0$)
$\begin{equation*}
C_{loss} = c_{el} \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt)
\end{equation*}$
with $c_{el}$ as the electricity cost. This is only valid when assuming $E_{BTMS}(k=0) = E_{BTMS}(k=T)$.

## 2. Level: Optimal day-ahead/long-term plan

in *planning()*:

$\begin{equation}
\begin{aligned} 
\min \quad a \cdot (P_{slack} - P_{free}) + b \cdot \Sigma_{k=0}^{T} P_{BTMS,Ch}(k)dt + c \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt) \\\ 
+\Sigma_{k=0}^{k=T} d(k) \cdot t_{L}(k)
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
E_{BTMS}(k) &\geq 0 \quad &\forall k \in [0,T]\\
E_{BTMS}(k) &\leq \Delta E_{BTMS} \quad &\forall k \in [0,T] \\
t_L(k) &\geq \frac{E_{Shift}(k+1)-E_{Shift}(k)}{P_{charge,avg}} \quad &\forall k \in [0,T]\\
t_L(k) &\geq 0 \quad &\forall k \in [0,T]\\
E_{BTMS}(0) &= E_{BTMS}(T+1)\\
P_{slack} &\geq \max(P_{Grid}(k))\\
P_{slack} &\geq P_{free}\\
\end{align}$
We added the BTMS size $\Delta E_{BTMS}$ to the constraint, and ensured that the energy level is between this and 0. Furthermore, we set $E_{BTMS}(0) = E_{BTMS}(T+1)$ to ensure, that the BTMS isn't completly discharged in our case of a one day simulation. For real-world use, optimization for 2 or 3 days in advance might be better solution, with just using the results for the first day.

Compared to the approach described in 1st level for determining BTMS-size, we added the ability to shift charging power, i.e. to increase charging time of vehicles. For this, we increase the state of shifted energy $E_{Shift}$ which serves as a stock for the shifted power and has an equal defintion of the earlier introduced energy lag. In order to be able to assign a meaningful cost to shifting energy, we value the cost of waiting time increase of vehicles (see equation 27). Each time the shifted energy increases, additional waiting time is necessary, which can be determined by the additional shifted energy divided by the average charge power of a vehicle $P_{charge,avg}$. If the shifted energy stays the same or is reduced, there is no additional waiting time necessary. The cost-function parameter $d(k)$ is defined for every timestep, so that e.g. higher waiting time cost at ride-hailing peak-demand times could be implemented, to further prioritize having enough available charging power at these times. 

**remark**: We might have to add a constraint to ensure that the shifted energy doesn't blow up, but ideally, the cost function should do this.

We define our state, control, disturbance and slack variables as:
$\begin{align}
x(k) &= [E_{BTMS}(k), E_{Shift}(k)]\\
u(k) &= [P_{Grid}(k), P_{BTMS}(k), P_{BTMS,Ch}(k), P_{BTMS,DCh}(k), P_{Shift}(k)] \\
i(k) &= [P_{Charge}(k)]\\
P_{slack}&, t_L
\end{align}$

From this, we can obtain a trajectory for the desired Energy Level in the behind the meter storage. From this, we determine a load band with a 5% upper and lower deviations of the BTMS-size $\Delta E_{BTMS}$. We apply the min- and max-function to ensure, that we don't exceed storage size with this.

$\begin{align}
E_{BTMS,traj,lower}(k) &= \max([0\text{kWh}, E_{BTMS}(k)-0.05\Delta E_{BTMS}])\\
E_{BTMS,traj,upper}(k) &= \min([\Delta E_{BTMS}, E_{BTMS}(k)+0.05\Delta E_{BTMS}])
\end{align}$

**Option**: We could also include predictions for power grid constraints like
$$\begin{equation*}
P_{Grid}(k) \leq P_{Grid,Limit,pred}(k) \quad \forall k \in [0,T] 
\end{equation*}$$