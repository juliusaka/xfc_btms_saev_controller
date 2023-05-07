# MPC Base

## two level approach

1. Level: economical optimization (sizing) of BTMS-size
    - for unconstrained case, i.e. all cars are charged immediatly.
2. Level: real-time trajectory following MPC algorithm

## 1. Level: Economical Optimization of BTMS-Size

in *determineBtmsSize()*:

see paper

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
which represents the energy loss correctly. Likewise, we are also able to implement the cost of the energy loss as ($P_{BTMS,DCh} \leq 0$)
$\begin{equation}
C_{loss} = c_{el} \cdot (\Sigma_{k=0}^{k=T} P_{BTMS,Ch}(k)dt + \Sigma_{k=0}^{k=T}P_{BTMS,DCh}(k)dt)
\end{equation}$
with $c_{el}$ as the electricity cost. This is only valid when assuming $E_{BTMS}(k=0) = E_{BTMS}(k=T+1)$.

## 2. Level: short horizoned model predictive control

see paper