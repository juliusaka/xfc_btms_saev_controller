# MPC Base

## three level approach

1. Level: economical optimization of BTMS-size
    - for unconstrained case, i.e. all cars are charged immediatly. 
    - Can apply before level 2 a factor to decrease the BTMS size, as this size should be seen as an upper limit, where charging of vehicle isn't decreased.
2. Level: optimal long-term/day-ahead plan for charging
3. Level: real-time trajectory following MPC algorithm

## 1. Level: Economical Optimization of BTMS-Size

$\begin{equation} 
\min \quad a \cdot (P_{slack} - P_{free}) + b \cdot \Sigma_{k=0}^{T} 0.5 |P_{BTMS}(k)|dt 
\end{equation}$
subject to:
$\begin{align} 
P_{Charge}(k) &= P_{Grid}(k) - P_{BTMS}(k) \quad &\forall k \in [0,T]  \\
E_{BTMS}(k+1) &= E_{BTMS}(k) + dt \cdot \eta \cdot P_{BTMS}(k) \quad &\forall k \in [0,T]\\ 
E_{BTMS}(0) &= E_{BTMS}(T+1)\\
E_{BTMS}(0) &= 0\\
P_{slack} &\geq \max(P_{Grid}(k))\\
P_{slack} &\geq P_{free}
\end{align}$

where $a$ is the demand charge per day, $b$ is the BTMS cost per cycle. $P_{Grid}$ is the power withdrawal from the electric grid, $P_{BTMS}$ is the power to/from the behind the meter storage and $P_{Charge}$ is the unconstrained power flow of the charging station, which is determined in the class-method *generatePredictions()*, with a simple algorithm, considering vehicle arrivals and the maximum number of available charging bays at the charging station. $E_{BTMS}$ is the energy content of the behind the meter storage, and its size is left open to be determined by the optimization. The objective is to minimize the sum of demand charge and the usage cost of the BTMS as the cost of storing/releasing energy in terms of cycles. As demand charges can be applied after exceeding a certain level, we choosed a formulation which returns the exceeding of a certain power level $P_{free}$. The term $P_{slack} - P_{free}$ is 0 as long as $\max(P_{Grid}) \leq P_{free}$, and gives after that the difference to the free power level. 

As the problem is convex in objective function and constraints, a solution can be efficiently determined with open-source accessible solvers. We use the mathematical modeling language *cvxpy*. For the implementation, we defined the following states, control and disturbance variables. We also define the slack variable for a free power level before demand charge:
$\begin{align}
x(k) &= [E_{BTMS}(k)] \\
u(k) &= [P_{Grid}(k), P_{BTMS}(k)] \\
d(k) &= [P_{Charge}(k)]\\
P_{slack}
\end{align}$

With this formulization, the BTMS-size is determined as $\max(E_{BTMS}) - \min(E_{BTMS})$. The maximum power delivery of the BTMS is unconstrained and can therefore reach high C-Ratings, especially when you choose high BTMS cycle cost compared to demand charges. Integrating a C-Rating into this optimization problem leads to a non-convex formulization which would have to be solved with a less efficient solver and isn't guarenteed to be globally optimal. As we try to assess future scenarios, higher C-ratings are probably possible, so that this shouldn't be off to much concern for us. 

After determining the BTMS-size for unconstrained charging, it is possible to reduce the size to e.g. assess the impact of this on SAEV-fleets.

## 2. Level: Optimal day-ahead/long-term plan