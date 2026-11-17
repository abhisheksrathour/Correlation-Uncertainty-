"""Full research manuscript and author-review companions with native Word math."""
import json,copy,re,subprocess
from pathlib import Path
import numpy as np,pandas as pd
from docx import Document
from docx.shared import Inches,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from optics import ROOT
import docx_layout as L

TITLE='Correlation uncertainty and nonlinear yield in broadband antireflection coating design'
L.TITLE=TITLE;OUT=ROOT/'output';D=ROOT/'data'
S=pd.read_csv(D/'primary_metrics.csv').set_index(['method','case'])
N=pd.read_csv(D/'nominal_metrics.csv').set_index('method')
CI=pd.read_csv(D/'paired_contrasts.csv')
RUNS=json.load(open(D/'all_design_runs.json'));SEL=json.load(open(D/'selected_designs.json'))
V=json.load(open(D/'validation.json'));REF=json.load(open(ROOT/'references/references.json'))
METHODS=['nominal','iid','common','learned','envelope','cvar']
LAB={'nominal':'NOM','iid':'IID','common':'CM','learned':'LW','envelope':'CE','cvar':'SCV'}
B=[];EQS=[]
def p(t,rev=False):B.append(dict(type='p',text=t,rev=rev))
def h(t,l=1):B.append(dict(type='h',text=t,level=l))
def page():B.append(dict(type='break'))
def eq(t,rev=False):EQS.append(t);B.append(dict(type='eq',index=len(EQS)-1,rev=rev))
def table(n,title,heads,rows,widths,rev=False,note=None):B.append(dict(type='table',title=f'Table {n} {title}',head=heads,rows=rows,widths=widths,rev=rev,note=note))
def fig(n,t,rev=False,width=6.5):
 number=4 if n==11 else n+1 if n>=4 else n
 B.append(dict(type='fig',number=number,text=t,rev=rev,width=width))
def pct(x):return f'{100*x:.2f}'
def q(method,case,metric):return S.loc[(method,case),metric]

ABSTRACT=(
'Layerwise thickness tolerances do not specify the joint errors that determine an optical coating spectrum. '
'This numerical study examines broadband antireflection design when error correlations are uncertain but marginal tolerances are known. '
'A dispersive transfer matrix model is combined with a fixed-marginal covariance envelope and compared with nominal, independent-error, common-mode, learned-covariance and sampled conditional-value-at-risk objectives. '
'The envelope is an established worst-variance identity; its usefulness as a nonlinear yield objective is tested rather than presumed. '
'Eight alternating silica–hafnia layers are optimized over 450–750 nm and audited with 4096 fresh fabrication-error draws per process case. '
'At a 4 nm tolerance and a 5% maximum-reflection specification, envelope design increases independent-error yield from 67.53% to 74.98%. '
'However, learned-covariance design achieves 76.20%, and the envelope design has a worse common-mode 95th-percentile reflection of 20.06%, compared with 13.16% for nominal design and 6.37% for sampled tail-risk design. '
'All reported yields are conditional on the synthetic optical and process models. '
'Independent scattering, energy, derivative and grid checks support numerical correctness, while restart, bias and heavy-tail audits expose remaining sensitivity. '
'The results show that a valid local covariance envelope can improve specification yield without controlling severe nonlinear failures. '
'Correlation uncertainty, the chosen risk metric and nonlinear validation must therefore be considered together when selecting a coating design.')

h('1 Introduction')
p('A broadband antireflection coating must suppress reflection across wavelength, incidence angle and polarization after deposition. Nominal spectral optimization can exploit interference cancellations that are fragile to small changes in optical thickness. Wide-angle visible antireflection design is already established in Optical Review {C1}, and the wider inverse-design literature spans conventional optimization and deep learning {C2}. The practical question considered here concerns the joint fabrication-error law, rather than the speed of predicting a nominal spectrum.')
p('Suppose a deposition process provides a credible root-mean-square tolerance for each layer, but only a small set of witness batches from which to estimate cross-layer correlation. An independent-error model, a shared deposition-rate error and an alternating error pattern can have identical marginal tolerances while producing different optical spectra. Treating these process models as interchangeable can change both the design and its apparent reliability.')
p('We examine a covariance-envelope design rule alongside five controls and evaluate every selected stack with a separate nonlinear optical audit. The contributions are a controlled fixed-marginal correlation comparison, an explicit distinction between reflection-specification yield and upper-tail loss, and numerical evidence on where a local uncertainty margin fails to predict the nonlinear outcome. The variance identity itself and robust optical-coating design are established ideas. No priority claim is made for either. The scope is an offline planar-coating simulation; the work does not contain a physically synchronized digital twin or fabricated samples.',True)

page();h('2 Literature review and research gap')
p('Robust coating design has a long history. Wiesmann et al. investigated evolutionary design of multilayer coatings {C3}. Dai et al. optimized spectral mean error and standard deviation using multiobjective search and local refinement {C4}. Their later error-perturbation study treats correlated and uncorrelated errors in broadband optical monitoring {C5}. Tikhonravov et al. describe both harmful correlation and useful error self-compensation {C6}. Correlation is therefore a physical feature of deposition and monitoring, not a newly discovered source of uncertainty.')
p('Recent work narrows the gap further. Ji et al. describe correlated-monitoring-error yield optimization in a 2026 conference paper {C7}. Ghapanvari introduces flow-matching inverse design with a conditional-value-at-risk objective {C8}. Poitras and Ma use surrogate sensitivity analysis and in-situ reoptimization for waveguide-facet coatings {C9}, where a simple plane-wave model can be inadequate. Venugopalan et al. combine coating optimization with fabrication-tolerance considerations and thickness inference {C10}. These studies preclude claims of a first yield-aware, correlation-aware or fabrication-aware coating optimizer.')
p('Learning also serves several distinct roles. Adaptive multiobjective coating design can use learned optimization initialization {C11}; deep inversion {C14} and OptoGPT {C15} address other inverse-design difficulties. Current examples include active-learning discrete-index antireflection design {C12}, bilayer metamaterial inversion {C13}, application-specific spectral losses {C24}, and constrained curved-substrate coating synthesis {C25}. Fabrication-conscious neural design includes systematic and random deposition imperfections {C16}. Sharpness-aware gradient design with differentiable transfer matrices targets perturbation-tolerant nonlocal films and includes a fabricated spatial-frequency filter {C23}. These related methods motivate the uncertainty audit; none is reproduced here as a common numerical benchmark.')
table(1,'Closest prior work and the question tested here',
 ['Prior direction','Uncertainty or task','Relationship to this study'],[
 ['Dai et al. {C4,5}','Statistical robustness and monitoring error','Sensitivity margins and Taylor error analysis are established'],
 ['Tikhonravov et al. {C6}; Ji et al. {C7}','Correlated deposition and yield','The present test treats correlation as uncertain at fixed marginals'],
 ['Ghapanvari {C8}','Generative design with tail-risk loss','Our sampled control tests the risk metric, not that generative model'],
 ['Poitras and Ma {C9}','Facet sensitivity and reoptimization','Different geometry; our model applies to a planar illuminated window'],
 ['Present study','Unknown correlation and nonlinear audit','Matched local designs, shared-process tests and retained adverse outcomes']],
 [1.6,2.0,3.2],rev=True)
p('The bounded research gap is whether a correlation-agnostic local variance envelope is a useful design proxy when judged by independent nonlinear yield and tail metrics. We do not infer this gap merely from the absence of a particular model name. The comparison isolates the covariance assumption, risk objective, optical degrees of freedom and evaluation grid. Its contribution is the resulting reproducible optical evidence and diagnostic workflow; exhaustive novelty priority remains unproven.',True)

page();h('3 Optical system and problem formulation')
p('Consider air, eight alternating SiO2/HfO2 layers, and a semi-infinite BK7 substrate. Layer 1 faces air. The low-index and high-index sequence is fixed so that only physical thickness is optimized. The vector of nominal thicknesses and the optical operating set are')
eq(r'\mathbf d\in[25,160]^8\ {\rm nm},\qquad a=(\lambda,\theta_0,p),\quad p\in\{s,p\}.')
p('Wavelength spans 450–750 nm and external angle spans 0–40 degrees. The design set contains 21 wavelengths, three angles and both polarizations. The independent audit uses 61 wavelengths, nine angles and both polarizations. This finite-grid target is explicitly distinguished from a continuous-band guarantee.')
eq(r'\widetilde{\mathbf d}=\mathbf d+\boldsymbol\delta,\qquad \boldsymbol\delta\sim{\cal N}(\mathbf0,\sigma^2\mathbf C),\quad C_{jj}=1.')
p('The primary tolerance is an absolute standard deviation of 4 nm in every layer. It is an assumed process scenario rather than a measured deposition capability. The real problem is to select a stack whose worst reflection remains below 5% with high probability, while limiting the severity of failures. Unknown correlation means that C is not fixed by the marginal tolerances. It does not mean that every covariance is physically likely.')
table(2,'Nomenclature and units',['Symbol','Meaning','Unit'],[
 ['d, d̃, δ','Nominal thickness, realized thickness and deposition error','nm'],
 ['λ, θ₀, p','Vacuum wavelength, external angle and polarization','nm; degree; —'],
 ['ñⱼ = nⱼ − iκⱼ','Complex refractive index of layer j','—'],
 ['uⱼ, qⱼ, δⱼ','Normal optical factor, admittance and layer phase','—'],
 ['Mⱼ, M','Layer characteristic matrix and total matrix','—'],
 ['r, t; R, T, A','Field amplitudes; reflected, transmitted and absorbed power fractions','—'],
 ['sₐ, Hₐ','Reflection sensitivity and Hessian at optical point a','nm⁻¹; nm⁻²'],
 ['σ, C, Σ','Marginal tolerance, correlation and covariance','nm; —; nm²'],
 ['Ĉ, γ','Learned correlation and shrinkage coefficient','—'],
 ['α, zα, β','Familywise linear-model risk, normal quantile and tail level','—'],
 ['τ, η','Smoothing temperature and tail-loss auxiliary variable','reflection fraction'],
 ['G, Y, N','Maximum reflection, specification yield and test-batch count','—'],
 ['NOM, IID, CM','Nominal, independent-error and common-mode objectives','—'],
 ['LW, CE, SCV','Learned covariance, correlation envelope and sampled CVaR','—']],
 [1.55,4.4,.85],rev=True)
p('Reflection is dimensionless throughout the equations. Percentages in tables and plots are 100 times the corresponding power fraction. All statistical results are simulations of this specified planar system.')

page();h('3.1 Pictorial system and optical assumptions',2)
fig(1,'Planar coating and uncertainty interfaces. The equal-height layer drawing is schematic. The three matrix icons illustrate correlations with the same unit diagonal; they are not measured process matrices',width=6.6)
p('Optical constants are drawn from the refractiveindex.info data collection {C17}. Hafnia uses the complex measured-film dispersion reported by Franta et al. {C18}, interpolated in wavelength without extrapolation. The 450 nm index is approximately 2.1266 − i9.23 × 10−5; absorption is retained. Fused silica uses the bulk Malitson dispersion {C19} as an explicitly transparent film proxy. BK7 uses the real Sellmeier dispersion in the SCHOTT catalogue dataset distributed with the database. Source YAML files, retrieval URLs and hashes are supplied with the code.')
p('The bulk-silica proxy does not account for film density, porosity or deposition-dependent dispersion. The substrate is treated as semi-infinite, so rear-surface reflection and finite-glass absorption are excluded. Layers are smooth, laterally uniform, isotropic and nonmagnetic. Index fluctuations, scatter, interface roughness, stress and thickness gradients are absent. These assumptions define a numerical design test and must be revisited before physical manufacture.')
eq(r'u_j=\sqrt{\widetilde n_j^{\,2}-\sin^2\theta_0},\qquad q_j^{(s)}=u_j,\qquad q_j^{(p)}=\frac{\widetilde n_j^{\,2}}{u_j}.')
p('The passive branch is selected consistently with the n − iκ index convention and propagation exp(−i2πuj z/λ). The phase of layer j is δj = 2πuj dj/λ. Both polarizations are tested separately, and the performance metric takes their maximum.')
eq(r'\mathbf M_j=\begin{bmatrix}\cos\delta_j&i\sin\delta_j/q_j\\ iq_j\sin\delta_j&\cos\delta_j\end{bmatrix},\qquad \mathbf M=\prod_{j=1}^{8}\mathbf M_j.')

page();h('3.2 Optical response and exact first derivatives',2)
p('Let q0 and qS denote incident-medium and substrate admittances. Writing the total matrix entries as Mmn gives two boundary combinations')
eq(r'b=M_{11}+q_S M_{12},\qquad c=M_{21}+q_S M_{22}.')
p('The field amplitudes and power coefficients follow from the optical boundary conditions:')
eq(r'r=\frac{q_0b-c}{q_0b+c},\qquad t=\frac{2q_0}{q_0b+c}.')
eq(r'R=|r|^2,\qquad T=\frac{{\rm Re}\,q_S}{{\rm Re}\,q_0}|t|^2,\qquad A=1-R-T.')
p('The substrate and air are transparent in this model, so the admittance power ratio in Eq. (7) is applicable. Absorptance is reported along with reflection to prevent an apparently antireflective design from concealing a large absorption loss. A separate recursive scattering calculation, independent of the matrix product, checks both R and T.')
p('Layer sensitivities are obtained analytically by differentiating each characteristic matrix. Prefix and suffix products allow the derivative of the stack matrix to be formed without re-solving a different physical model:')
eq(r'\frac{\partial\mathbf M}{\partial d_j}=\left(\prod_{k<j}\mathbf M_k\right)\frac{\partial\mathbf M_j}{\partial d_j}\left(\prod_{k>j}\mathbf M_k\right).')
eq(r's_{a,j}=\frac{\partial R_a}{\partial d_j}=2\,{\rm Re}\!\left(r_a^*\frac{\partial r_a}{\partial d_j}\right).')
p('The amplitude derivative uses the quotient rule in Eq. (6). The Hessian needed to differentiate a sensitivity margin is evaluated by central differences of the analytic sensitivity, with a 0.002 nm step. Central differences of the full optical response and of each training objective provide separate implementation checks. The forward model is not a neural surrogate; statistical learning enters only through the covariance baseline.')
p('Absorption at the long-wavelength end of the selected hafnia data is negligible, while it remains finite near 450 nm. This wavelength dependence is carried through every design and test calculation. No refractive index is fitted to improve the reported yields.',True)

page();h('4 Covariance envelope and local reliability')
h('4.1 Known marginal tolerances and unknown correlation',2)
p('At a fixed nominal stack, a Taylor expansion separates the linear uncertainty model from its neglected curvature. Here ξ lies on the segment between nominal and realized thicknesses:')
eq(r'R_a(\mathbf d+\boldsymbol\delta)=R_a(\mathbf d)+\mathbf s_a^{\mathsf T}\boldsymbol\delta+\tfrac12\boldsymbol\delta^{\mathsf T}\mathbf H_a(\boldsymbol\xi)\boldsymbol\delta.')
p('The uncertainty set contains every positive-semidefinite correlation matrix with the specified unit diagonal:')
eq(r'{\cal C}=\{\mathbf C=\mathbf C^{\mathsf T}\succeq0:\ {\rm diag}(\mathbf C)=\mathbf1\}.')
p('For any fixed C, the variance of the linear response increment is')
eq(r'v_a(\mathbf C)=\sigma^2\mathbf s_a^{\mathsf T}\mathbf C\mathbf s_a.')
p('The familiar fixed-diagonal worst-variance identity yields the envelope')
eq(r'\sup_{\mathbf C\in{\cal C}}v_a(\mathbf C)=\sigma^2\|\mathbf s_a\|_1^2.')
p('For completeness, positive semidefiniteness and unit diagonal imply |Cjk| ≤ 1. Therefore')
eq(r'\mathbf s_a^{\mathsf T}\mathbf C\mathbf s_a\leq\sum_{j,k}|s_{a,j}||s_{a,k}|=\|\mathbf s_a\|_1^2,\qquad \mathbf C_a^\star=\mathbf u_a\mathbf u_a^{\mathsf T},\quad u_{a,j}={\rm sign}(s_{a,j}).')
p('The rank-one matrix on the right attains the bound; any sign may be chosen when a sensitivity is zero. This short derivation is included for reproducibility and is not presented as a new theorem. A different optical point can have a different maximizing sign pattern. The envelope is consequently a set of pointwise variance bounds, not a claim that one physical process simultaneously attains every bound.')
h('4.2 Four choices of uncertainty margin',2)
eq(r'\begin{aligned}b_a^{\rm IID}&=\sigma\|\mathbf s_a\|_2,&b_a^{\rm CM}&=\sigma|\mathbf1^{\mathsf T}\mathbf s_a|,\\ b_a^{\rm LW}&=\sigma\sqrt{\mathbf s_a^{\mathsf T}\widehat{\mathbf C}\mathbf s_a},&b_a^{\rm CE}&=\sigma\|\mathbf s_a\|_1.\end{aligned}')
p('These margins control different directions in thickness space. Common-mode cancellation can be favorable at one wavelength and unfavorable at another. The envelope removes the correlation estimate by paying for the sign-aligned direction at each optical point. Whether that larger local margin produces a better nonlinear design is the empirical question tested below.')

page();h('4.3 Learning covariance and optimizing a smooth margin',2)
p('The learned-covariance control uses 32 independent synthetic witness batches generated from AR(0.6) correlation. Ledoit–Wolf shrinkage {C20} regularizes the sample covariance toward a scaled identity. Because marginal tolerance is assumed known, diagonal normalization retains only the learned correlation:')
eq(r'\widehat{\boldsymbol\Sigma}=(1-\gamma)\mathbf S+\gamma\frac{{\rm tr}\,\mathbf S}{8}\mathbf I,\qquad \widehat{\mathbf C}=\mathbf D^{-1/2}\widehat{\boldsymbol\Sigma}\mathbf D^{-1/2},\quad \mathbf D={\rm diag}(\widehat{\boldsymbol\Sigma}).')
p('This is statistical learning from explicitly simulated process records. There is no trained deep network and no measured witness wafer. Test draws are excluded from covariance fitting. The margin objectives use a one-sided normal quantile allocated across the M = 126 design constraints:')
eq(r'z_\alpha=\Phi^{-1}(1-\alpha/M),\qquad \alpha=0.05,\qquad U_a(\mathbf d)=R_a(\mathbf d)+z_\alpha b_a(\mathbf d).')
p('A union bound provides a finite-grid statement for the Gaussian linearized model: if every Ua is at most the reflection specification, the probability of any linearized constraint violation is at most α for every fixed C in the uncertainty set. No independence across optical points is needed. The condition does not cover the Taylor remainder, a nonzero error mean, non-Gaussian errors or a continuous wavelength interval.')
eq(r'\min_{\mathbf d\in[25,160]^8}\ F_\tau(\mathbf d),\qquad F_\tau=\tau\log\sum_{a=1}^{M}\exp\!\left(\frac{U_a(\mathbf d)}{\tau}\right),\quad \tau=5\times10^{-4}.')
p('The nominal control sets ba = 0. The smooth maximum differs from the exact maximum by at most τ log M. For CE, |s| is replaced during optimization by the negligible smoothing sqrt(s2 + 10−18), with sensitivity expressed per nanometer. All objectives use the same thickness bounds and starts. An optimizer stop is a local numerical outcome, not evidence of a global optimum.')
h('4.4 Nonlinear sampled tail risk control',2)
p('An in-house sampled conditional-value-at-risk control follows the standard variational formulation {C21}. It uses 64 fixed training errors, equally divided among independent, common, AR(0.6) and AR(−0.6) processes. This control evaluates the nonlinear optical model during design:')
eq(r'\min_{\mathbf d,\eta}\ \eta+\frac{1}{(1-\beta)B}\sum_{b=1}^{B}{\rm sp}_\tau\!\left(g_b(\mathbf d)-\eta\right),\quad \beta=0.95,\quad B=64.')
eq(r'g_b=\tau\log\sum_a\exp\!\left(\frac{R_a(\mathbf d+\boldsymbol\delta_b)}{\tau}\right),\qquad {\rm sp}_\tau(x)=\tau\log(1+\exp(x/\tau)).')
p('The sampled loss emphasizes the upper tail rather than the probability of satisfying a fixed 5% specification. It is a deliberately strong mechanism control, but it is not a reimplementation of the flow-matching architecture in {C8}. Its training process mixture differs from the single AR process used for covariance learning, and this information difference is reported rather than concealed.',True)

page();h('4.5 Optimization workflow',2)
fig(2,'Flowchart of the matched optical-design comparison. The optimization loop repeats for each objective and each common start. Solver flags and budget stops are retained before selecting the lowest training objective',width=6.05)
B.append(dict(type='algorithm',title='Algorithm 1 Covariance aware design and independent nonlinear audit',lines=[
'Input  Optical constants, layer sequence, bounds, design grid, σ, α, starts and disjoint random seeds',
'1  Generate training witnesses and the fixed sampled-risk training errors; fit only the LW correlation',
'2  For each objective and each common start, evaluate optical responses and required derivatives',
'3  Update bounded thicknesses until convergence or the fixed iteration budget; retain every solver record',
'4  Select the smallest training objective within each method without consulting test yield',
'5  Generate new shared-process error draws; compute dense-grid maximum R, minimum T and maximum A',
'6  Report specification yield with intervals, reflection tail metrics and linearization discrepancies',
'Output  Designs and raw audit records, including adverse cases and physically invalid draws']))
p('The proposed workflow solves the uncertainty-selection problem by exposing how covariance assumptions change the design and by verifying each candidate with the full nonlinear response. It does not declare a design reliable solely because a local margin was minimized. This distinction becomes decisive in the common-mode results.',True)

page();h('5 Numerical study design')
h('5.1 Frozen primary protocol and controls',2)
p('The numerical protocol was frozen before primary optimization or test generation. Development used separate seeds to check the model and obtain one useful nominal starting point. Every primary method receives that same start plus five independent uniform starts. The smallest final training objective selects one design per method. All 36 optimization records are preserved.')
table(3,'Primary configuration and independent audit',['Item','Frozen setting'],[
 ['Optical system','Air / (SiO2/HfO2)4 / semi-infinite BK7'],
 ['Design degrees of freedom','Eight thicknesses, each 25–160 nm; no material or layer-count search'],
 ['Optical band and field of view','450–750 nm; 0–40 degrees; separate s and p polarizations'],
 ['Design grid','21 wavelengths × 3 angles × 2 polarizations = 126 points'],
 ['Independent audit grid','61 wavelengths × 9 angles × 2 polarizations = 1098 points'],
 ['Marginal error and specification','σ = 4 nm; max R ≤ 0.05'],
 ['Covariance learning','32 AR(0.6) witness batches; seed 2101; Ledoit–Wolf shrinkage'],
 ['Sampled-risk training','64 mixture draws; seed 2102; β = 0.95'],
 ['Primary optimizer','Six common starts; L-BFGS-B; max 220 iterations; ftol 1e-11; gtol 2e-7'],
 ['Test population','4096 fresh Gaussian batches per case; seed 2201; shared draws across designs'],
 ['Primary process cases','IID; common; alternating; AR ±0.6; two-layer block; one random PSD correlation'],
 ['Separate stress case','Fixed sign-aligned rank-one process selected for each design'],
 ['Intervals and contrasts','95% Wilson yield intervals; 2000 paired bootstrap resamples for shared-process contrasts']],
 [1.9,4.9])
p('Each process case is a distinct distribution shift. The cases are not pooled into a claimed manufacturing population. The block matrix combines a 0.2 global component with 0.8 common error within adjacent layer pairs. The random positive-semidefinite correlation is generated once with seed 2202 and then fixed. Both have the same unit diagonal as the other cases.')
h('5.2 Separate sign stress and physical validity',2)
p('For each selected design, the optical design point with the largest CE margin supplies a fixed sensitivity sign vector. Its rank-one correlation defines one sign-aligned Gaussian process before test draws are generated. This stress is design-dependent, so its outcomes cannot be interpreted as a paired comparison under one common manufacturing process. It is also not an exhaustive nonlinear worst-case search.')
p('Nonpositive realized thickness is counted as a fabrication failure, without rejection sampling. Its failure penalty is infinite for tail summaries, while optical absorption and transmission are undefined. All primary Gaussian test draws are physically valid. The later heavy-tail audit contains a few invalid draws, whose masks and counts are explicitly retained.')

page();h('5.3 Reliability metrics and numerical verification',2)
p('For the dense audit set Atest, define the nonlinear maximum reflection and its empirical specification yield as')
eq(r'G_b=\max_{a\in{\cal A}_{\rm test}}R_a(\mathbf d+\boldsymbol\delta_b),\qquad \widehat Y=\frac1N\sum_{b=1}^{N}{\bf1}\{G_b\leq0.05,\ \mathbf d+\boldsymbol\delta_b>\mathbf0\}.')
p('We report the 95th and 99th percentiles of G, the average of its largest ceil(0.05N) values, maximum observed absorptance and minimum transmittance. The upper-five-percent mean uses this stated finite-sample convention. Wilson score intervals {C22} quantify conditional binomial uncertainty in yield:')
eq(r'\frac{\widehat Y+z^2/(2N)\ \pm\ z\sqrt{\widehat Y(1-\widehat Y)/N+z^2/(4N^2)}}{1+z^2/N},\qquad z=\Phi^{-1}(0.975).')
p('Paired bootstrap yield differences use the common error draws within a process case. These intervals do not include optical-model mismatch, material uncertainty, optimization-basin uncertainty or the uncertainty of a future factory process. They are pointwise intervals; no simultaneous multiple-comparison claim is made.')
table(4,'Independent verification of the optical implementation',['Check','Maximum absolute discrepancy','Interpretation'],[
 ['Bare interface versus Fresnel law',f"{V['bare_fresnel_max_abs']:.2e}",'Zero-layer boundary condition'],
 ['Single quarter-wave layer',f"{V['quarterwave_max_abs']:.2e}",'Analytical interference reference'],
 ['Lossless R + T = 1',f"{V['lossless_energy_max_abs']:.2e}",'Power conservation'],
 ['Recursive versus matrix reflection',f"{V['recursive_R_max_abs']:.2e}",'Independent optical calculation'],
 ['Recursive versus matrix transmission',f"{V['recursive_T_max_abs']:.2e}",'Independent power calculation'],
 ['Analytic thickness Jacobian',f"{V['jacobian_max_abs']:.2e}",'Central differences of full response'],
 ['Five objective gradients',f"{max(V['objective_gradient_errors'].values()):.2e}",'Central differences of training objectives']],
 [2.45,1.55,2.8],rev=True)
p('Refining the nominal evaluation to 1 nm and 1 degree changes maximum reflection by at most 2.23 × 10−5 in power fraction across the six designs. A separate 256-draw AR(0.6) audit on a 2.5 nm/2.5 degree grid changes an individual sampled maximum by at most 7.89 × 10−4. One CE classification changes; the other five designs have unchanged yield on those draws. This supports grid adequacy for the reported comparison while preserving the finite-grid qualification.',True)
h('5.4 Reproducibility and generative assistance',2)
p('The package includes the frozen protocol and hash, material data, synthetic witness arrays, all design runs, raw test errors, per-batch metrics and figure code. Python 3.12, NumPy 2.3.5, SciPy 1.17.0 and scikit-learn 1.8.0 were used with one numerical thread. ChatGPT assisted with research framing, source discovery, mathematical exposition, code generation and execution, manuscript drafting, and figure preparation. This assistance exceeds copy editing and is disclosed here. Human authors must independently validate the scientific content, establish authorship and approve the manuscript before submission.',True)

page();h('6 Simulation results')
h('6.1 Nominal performance and selected thicknesses',2)
p('Figure 3 shows the maximum nominal reflection over angle and polarization at each wavelength. Table 5 supplies the optimized thicknesses in fabrication order. All six selected solutions originate from the shared development-informed start. None comes from a uniformly sampled start. The comparison therefore concerns local refinement within an accessible nominal basin, rather than six independently established global optima.')
fig(3,'Nominal optical behavior and selected designs. (a) Maximum reflection over the nine audit angles and both polarizations at each wavelength. (b) Layer thicknesses from the air-facing surface. The nominal spectral plot uses 301 wavelengths',width=6.5)
table(5,'Selected thicknesses in nanometers',['Rule']+[f'd{j}' for j in range(1,9)],
 [[LAB[m]]+[f'{x:.3f}' for x in SEL[m]['d']] for m in METHODS],[.80]+[.75]*8,
 note='The sequence is SiO2, HfO2, SiO2, HfO2, SiO2, HfO2, SiO2, HfO2. Digits support reproducibility and do not imply subpicometer fabrication accuracy.')
page()
table(6,'Nominal optical audit and local uncertainty diagnostic',['Rule','Max R (%)','Min T (%)','Max A (%)','CE margin (%)'],[
 [LAB[m],pct(N.loc[m,'maxR']),pct(N.loc[m,'minT']),pct(N.loc[m,'maxA']),pct(pd.read_csv(D/'linear_feasibility_diagnostic.csv').set_index('method').loc[m,'envelope_margin_max'])] for m in METHODS],
 [1.05,1.25,1.45,1.45,1.60],rev=True)
p('The nominal rule reaches 2.14% maximum reflection, while CE reaches 2.55% and SCV reaches 4.19%. At 4 nm tolerance, even the optimized CE margin is 12.31%, above the 5% specification. The sufficient linearized 95% reliability condition is therefore not satisfied. No 95%-yield certificate is claimed for these designs. The frozen-stack diagnostic would require approximately 1.03 nm tolerance for CE to satisfy that local condition on the design grid.',True)
fig(11,'Deterministic post-review optical mechanism audit. (a) Maximum reflection under an identical displacement of every layer, without random error. The dotted line is the 5% specification. (b) CE reflection spectrum versus common displacement, maximized over audit angles and polarization. This trajectory is not a measured fabrication distribution',rev=True,width=6.5)
p('The common-displacement trajectory explains why a local sensitivity objective can be misleading. The design moves through a curved interference landscape rather than a straight response line. The maximum may switch wavelength as layers change together, and a design that stays below the specification for many small displacements can rise rapidly at larger displacement. The spectral map resolves that mechanism directly. Its 97 deterministic offsets were evaluated after internal review; they did not alter the primary designs, test threshold or Monte Carlo records.',True)

page();h('6.2 Yield changes with the process correlation',2)
fig(4,'Primary simulated specification yield in percent from 4096 fresh draws per cell at 4 nm tolerance. Seven shared process cases lie left of the separator. The rightmost column uses a different fixed sign-aligned process for each design',width=6.6)
p('The same nominal stack has 58.84% yield under the block process and 95.58% under alternating errors, despite identical per-layer tolerances. CE improves yield over NOM in every shared primary process case. For independent errors the gain is 7.45 percentage points, with a paired 95% interval of 6.05–8.79 points. However, CE is below LW in five shared cases, equal in AR(−0.6), and above LW only for alternating errors. The envelope is therefore not the best general yield rule in this experiment.',True)
rows=[]
for case,name in [('iid','IID'),('common','Common'),('alternating','Alternating'),('ar0.6','AR +0.6'),('ar-0.6','AR −0.6'),('block','Block'),('random','Random PSD')]:
 r=CI[(CI.case==case)&(CI.comparison=='learned')].iloc[0]
 rows.append([name,pct(q('envelope',case,'yield_rate')),f"{pct(q('envelope',case,'yield_low'))}–{pct(q('envelope',case,'yield_high'))}",f'{100*r.difference:+.2f}',f'{100*r.low:+.2f} to {100*r.high:+.2f}'])
table(7,'CE yield and paired difference relative to learned covariance',['Process','CE yield (%)','Wilson 95% interval','CE minus LW (pp)','Paired 95% interval'],rows,[1.25,1.10,1.65,1.35,1.45],
 note='pp denotes percentage points. Wilson intervals describe a single design and process. Bootstrap intervals use paired error draws and are pointwise rather than simultaneous.',rev=True)
p('The lowest observed yield over the seven common process cases is 58.84% for NOM, 64.97% for LW and 62.62% for CE. These are minima over the finite tested family, not worst-case yields over all correlation matrices. The design-dependent sign column is reported separately: its stress severity depends on the selected stack and local sensitive point.')

page();h('6.3 Specification yield and reflection tail severity disagree',2)
fig(5,'Empirical distributions of nonlinear maximum reflection under independent, common-mode and AR(−0.6) processes. The vertical dotted line marks the 5% specification. Curves extend beyond the displayed 25% range in some common-mode cases',width=6.5)
p('Common-mode errors expose the most important metric disagreement. CE has 81.93% specification yield, above NOM at 75.42%, yet CE has a worse 95th-percentile maximum reflection: 20.06% compared with 13.16%. Increasing the mass below one threshold does not require a lighter far tail. The spectral response to a coherent thickness displacement is nonlinear and can leave the local cancellation region.')
tail=pd.read_csv(D/'postreview_tail_bootstrap.csv').set_index('estimand')
p(f"A post-review paired bootstrap with 2000 resamples of the frozen common-mode observations gives a CE-minus-NOM 95th-percentile reflection difference of {100*tail.loc['CE_minus_nominal','estimate']:.2f} percentage points, with a 95% interval of {100*tail.loc['CE_minus_nominal','low']:.2f}–{100*tail.loc['CE_minus_nominal','high']:.2f}. The corresponding CE-minus-SCV difference is {100*tail.loc['CE_minus_cvar','estimate']:.2f} points, with an interval of {100*tail.loc['CE_minus_cvar','low']:.2f}–{100*tail.loc['CE_minus_cvar','high']:.2f}. These pointwise intervals describe sampling uncertainty conditional on the selected designs and common-mode process.",True)
table(8,'Common-mode nonlinear reflection distribution',['Rule','Yield (%)','95th R (%)','99th R (%)','Upper 5% mean R (%)'],[
 [LAB[m],pct(q(m,'common','yield_rate')),pct(q(m,'common','q95')),pct(q(m,'common','q99')),pct(q(m,'common','cvar95'))] for m in METHODS],
 [1.05,1.20,1.45,1.45,1.65],rev=True)
p('The SCV control reduces common-mode 95th-percentile reflection to 6.37%, but its independent-error yield is only 49.17%. Its loss rewards smaller severe failures across the training mixture, rather than maximizing the number of batches below 5%. This behavior is consistent with the different objective and should not be described as failure of the CVaR concept. Its convergence limitation is examined separately in Section 6.6.')
p('No baseline dominates both reliability measures across the tested processes. Selecting a design therefore requires an application-specific choice between the frequency and severity of reflection failures. Reporting only yield would favor some designs whose rare optical loss remains substantial; reporting only a tail average would obscure the change in ordinary specification compliance.',True)

page();h('6.4 Tolerance and correlation sensitivity',2)
fig(6,'Prespecified sensitivity curves from fresh synthetic draws. (a–c) Fixed primary designs evaluated at 0, 2, 4, 6 and 8 nm tolerance, with 512 draws per point and process. (d) AR correlation sweep at 4 nm with 1024 draws per coefficient. Lines connect tested points and do not imply monotonic interpolation',width=6.45)
p('Tolerance reduction gives the clearest reliability improvement in Fig. 6a–c. At 2 nm, several local-margin designs are close to complete compliance, while performance deteriorates strongly by 6–8 nm. Reoptimizing the designs at each plotted tolerance was not part of this sweep: it tests the robustness of the same selected stacks. The data should therefore not be read as the optimal yield attainable at each process capability.')
p('Figure 6d shows that the sign and magnitude of AR correlation matter, rather than only an overall correlation strength. Strong negative correlation is relatively favorable for these selected stacks. Yield falls near small positive correlation before increasing again toward 0.9. A single monotone penalty on correlation magnitude would miss this behavior. The optical sensitivity pattern and the nonlinear displacement trajectory determine which correlation is harmful.')
p('The 4 nm points in Fig. 6 use a different, smaller Monte Carlo population from Fig. 4. Their numerical differences are sampling variation, not a change in model or test threshold. Confidence intervals are supplied in the underlying CSV files; the curves are descriptive and no trend significance test is asserted.')

page();h('6.5 Linearization learning and optimization basin sensitivity',2)
fig(7,'Three diagnostics. (a) Linearized and nonlinear 95th-percentile maximum reflection for IID, common and AR(0.6), one marker per design and process; the dotted line is equality. (b) Learned-covariance refits with four witness counts; each point uses an independent witness seed. (c) IID yield from every common optimizer start, using 512 new draws per design',width=6.55)
eq(r'\epsilon_b=G_b-\max_{a\in{\cal A}_{\rm test}}\{R_a(\mathbf d)+\mathbf s_a^{\mathsf T}\boldsymbol\delta_b\}.',rev=True)
p('The discrepancy in Eq. (23) compares maxima and can be positive or negative; it is not the pointwise Taylor remainder at one fixed optical condition. For NOM under independent errors, the linearized 95th percentile is 6.06%, whereas the nonlinear value is 8.35%. For CE under common-mode errors, the nonlinear tail moves much further above the local prediction. A mathematically correct variance bound can consequently be a poor optimizer of the nonlinear tail.')
p('More witness batches reduce covariance estimation error without producing monotone yield gains in this single-seed-per-count study. The Frobenius error relative to AR(0.6) falls from 1.65 with eight witnesses to 0.21 with 512. AR(0.6) yield ranges from 69.34% to 74.41%, while common-mode yield fluctuates. Covariance estimation accuracy and coating yield are different targets, and this small sweep does not estimate a learning curve across repeated training populations.',True)
p('The restart audit is equally consequential. Many uniform starts converge to stacks with zero specification yield; the median IID yield over six starts is zero for every objective. All selected primary designs come from the one common development-informed start. The reported performance therefore requires a useful initialization. A future comparison should combine a global search or broader multistart budget with these same covariance and nonlinear audits.',True)

page();h('6.6 Post review convergence and distribution shift audits',2)
p('Internal review identified the selected SCV solution as iteration-limited at the primary budget. A separate continuation allows up to 660 additional iterations from every selected design, with unchanged training data. Five rules terminate immediately at their previous local solution; SCV converges after 352 continuation iterations. Its training objective decreases from 0.064200 to 0.064054. New test draws preserve the yield-versus-tail tradeoff.',True)
cont=pd.read_csv(D/'continuation_audit.csv')
table(9,'SCV convergence audit on 1024 fresh paired draws',['Process','Primary yield (%)','Continued yield (%)','Primary 95th R (%)','Continued 95th R (%)'],[
 [name]+[pct(cont[(cont.method=='cvar')&(cont.case==case)&(cont.design==v)].iloc[0][metric]) for metric in ['yield_rate','q95'] for v in ['primary','continued']]
 for case,name in [('iid','IID'),('common','Common'),('block','Block')]], [1.0,1.35,1.5,1.4,1.55],rev=True,
 note='These are post-review test populations, not replacements for the frozen primary results.')
fig(8,'Exploratory distribution shifts outside the zero-mean Gaussian design assumptions. (a) Coherent thickness bias plus 2 nm independent Gaussian residual, 512 paired draws per point. (b) Independent or shared Student-t innovations with five degrees of freedom and 4 nm marginal RMS, 2048 draws; plain bars are IID and hatched bars common-mode, with 95% Wilson intervals',rev=True,width=6.5)
p('At zero bias and 2 nm residual tolerance, CE yield is 99.80%. A +4 nm coherent bias lowers it to 51.95%, whereas a −4 nm bias gives 92.77%. This asymmetry is outside the zero-mean covariance model and follows from the nonlinear optical trajectory. The heavy-tail audit does not uniformly reduce threshold yield: additional central mass can coexist with rarer extreme failures. One or two nonpositive-thickness draws per design/process are counted as failures. No finite upper-tail mean is reported for a population containing the infinite fabrication-failure penalty.',True)

page();h('6.7 Computational cost and design implications',2)
fig(9,'Optimization diagnostics on one host with one numerical thread. (a) Selected-start training traces; objective definitions differ and their numerical levels are not directly comparable. (b) Total measured time over six starts. Timing includes trace callbacks and excludes optical-model construction and nonlinear test generation',rev=True,width=6.5)
table(10,'Primary optimizer diagnostics',['Rule','Total time (s)','Selected iterations','Selected evaluations','Selected status'],[
 [LAB[m],f"{sum(r['seconds'] for r in RUNS if r['method']==m):.2f}",str(SEL[m]['nit']),str(SEL[m]['nfev']),'Converged' if SEL[m]['success'] else 'Budget reached'] for m in METHODS],
 [1.05,1.35,1.35,1.55,1.5],
 note='Iteration budgets are matched, but per-iteration optical workloads differ. These host timings were recorded before concurrent evaluation jobs and are not portable performance guarantees.')
p('CE uses a sensitivity Hessian approximation during optimization, whereas SCV propagates 64 nonlinear scenario stacks. Their unequal physical workloads explain why a shared iteration budget is not a shared compute budget. The total primary audit required approximately 331 s on the recorded host while other independent analyses were also running. This audit cost is omitted from Fig. 9b and should be included when planning a full design campaign.')
p('The practical sequence supported by these results is to characterize marginal tolerances, estimate plausible correlations, compare a covariance envelope with learned and sampled-risk controls, and retain only conclusions that survive nonlinear testing. If a required 95% yield is unavailable even in the local model, process improvement or a larger design space is needed. Minimizing a risk score alone does not supply the missing feasibility evidence.',True)
page();h('7 Limitations and physical validation requirements')
p('The main limitation is the restricted optical and fabrication model. A single eight-layer sequence and substrate are tested, with published hafnia optical constants and a bulk-silica proxy. The absolute tolerances are hypothetical; no deposition-monitoring record is used to establish the Gaussian laws, correlation family or stationarity across design thickness. A physical process may produce correlations that depend on layer sequence, material and monitoring strategy. That design dependence is omitted here.')

p('The uncertainty study is finite. Seven shared covariance cases, one random matrix and a design-dependent sign stress do not exhaust all positive-semidefinite correlations. The first-order envelope is exact only as a variance identity for the linear response. It omits mean shifts and curvature and does not provide nonlinear distribution-free reliability. The sampled-risk control uses only 64 fixed scenarios. Its larger training mixture and the covariance baseline’s narrower training law mean that the comparison is informative about design choices, not a proof of statistical minimax optimality.')
p('Optimization is local and strongly initialization-dependent. Although all methods receive identical starts and budgets, the selected designs arise from one useful nominal basin. The limited restart audit exposes that dependence rather than resolving it. Sampling intervals condition on the selected designs; they are not uncertainty intervals over optimizer runs, training seeds, material specimens or laboratories. The witness-count sweep likewise uses one training realization per count.')
p('An experimental validation should measure complex film dispersion and repeated layer-thickness errors from the intended deposition tool, reserve independent fabrication batches, and characterize reflection and transmission over wavelength, angle and polarization. Those records would permit a process-dependent covariance model and an audit of optical mismatch. Roughness, index-thickness correlation, thickness gradients and substrate back-surface effects should be added before the computed yields are interpreted as fabrication forecasts. These measurements remain future work.')
page();h('8 Conclusion')
p('Equal marginal thickness tolerances can produce very different nonlinear coating reliability when cross-layer correlations change. In the executed eight-layer planar study, correlation-envelope design improves independent-error yield from 67.53% to 74.98% but remains below the learned-covariance control at 76.20%. More seriously, its common-mode 95th-percentile reflection is 20.06%, despite improved specification yield. Sampled tail-risk design reduces that percentile to 6.37% while sacrificing independent-error compliance. The resulting contribution is an auditable design comparison and a demonstrated separation between local variance control, threshold yield and severe optical loss. Independent optical and grid checks support the computation, while initialization and model limitations bound its applicability. A covariance envelope should be used as a diagnostic design component and followed by nonlinear, process-specific reliability evaluation.',True)
h('Statements and Declarations')
p('Data and code availability. The accompanying package contains synthetic inputs, per-batch outputs, optimizer records, material provenance and executable reproduction scripts. A public repository DOI must be added by the responsible authors after independent validation and deposition of the approved files. No public data identifier is asserted here.')
p('Author information and declarations pending. Names, affiliations, correspondence, ORCIDs, author contributions, funding, competing interests, prior dissemination, concurrent-submission status and all-author approval must be supplied and verified by the actual authors. No absence of funding or conflicts is assumed. This work contains no human or animal study.')
p('Generative assistance is disclosed in Section 5.4. The submitting authors retain responsibility for scientific verification, the final text and all submission statements.')

page();h('References')

# Renumber bibliography by first appearance, including compact literature table.
order=[]
def cite(t):
 def repl(match):
  ids=[int(x) for x in match.group(1).split(',')]
  for n in ids:
   if n not in order:order.append(n)
  return '['+', '.join(str(order.index(n)+1) for n in ids)+']'
 return re.sub(r'\{C([\d,]+)\}',repl,t)
for b in B:
 if 'text' in b and b.get('number')!=4:
  b['text']=re.sub(r'(Figure |Fig\. )([4-9])(?=[a-z]|\b)',lambda m:m.group(1)+str(int(m.group(2))+1),b['text'])
 if 'text' in b:b['text']=cite(b['text'])
 if 'title' in b:b['title']=cite(b['title'])
 if 'rows' in b:b['rows']=[[cite(str(v)) for v in row] for row in b['rows']]
assert set(order)==set(range(1,26)),order
for new,old in enumerate(order,1):B.append(dict(type='ref',number=new,text=REF[old-1]['text']))
(ROOT/'references/citation_order.json').write_text(json.dumps({str(i+1):old for i,old in enumerate(order)},indent=2))

def prepare_math():
 for i,e in enumerate(EQS):
  e=re.sub(r'\{\\rm\s+([^}]+)\}',r'\\mathrm{\1}',e)
  e=re.sub(r'\{\\cal\s+([^}]+)\}',r'\\mathcal{\1}',e)
  e=e.replace(r'{\bf1}',r'\mathbf{1}')
  e=e.replace(r'\mathrm{nm}',r'\text{nm}')
  for operator in ['Re','diag','tr','sign','sp']:
   e=e.replace(r'\mathrm{'+operator+'}',r'\operatorname{'+operator+'}')
  if i==13:
   e=e.replace(r'\qquad \mathbf C_a^\star',r'\\ \mathbf C_a^\star')
   e=r'\begin{aligned}'+e+r'\end{aligned}'
  if i==15:
   e=e.replace(r'\qquad \widehat{\mathbf C}',r'\\ \widehat{\mathbf C}')
   e=r'\begin{aligned}'+e+r'\end{aligned}'
  EQS[i]=e
 f=ROOT/'qa/equations.md';f.write_text('\n\n'.join('$$\n'+e+'\n$$' for e in EQS))
 out=ROOT/'qa/equations.docx';subprocess.run(['pandoc',str(f),'-o',str(out)],check=True)
 d=Document(out);L.omml=[copy.deepcopy(x) for x in d.element.xpath('.//m:oMath')]
 assert len(L.omml)==len(EQS)
def link(doc,para,url):
 x=OxmlElement('w:hyperlink');x.set(qn('r:id'),doc.part.relate_to(url,RT.HYPERLINK,is_external=True))
 r=OxmlElement('w:r');p0=OxmlElement('w:rPr');fs=OxmlElement('w:sz');fs.set(qn('w:val'),'20');p0.append(fs);r.append(p0);t=OxmlElement('w:t');t.text=url;r.append(t);x.append(r);para._p.append(x)
def addfigure(doc,b,hilite):
 pp=doc.add_paragraph();pp.alignment=WD_ALIGN_PARAGRAPH.CENTER;pp.paragraph_format.keep_with_next=True;pp.paragraph_format.space_after=Pt(3)
 pp.add_run().add_picture(str(ROOT/'figures'/f"Fig{b['number']}.png"),width=Inches(b['width']))
 pp._p.xpath('.//wp:docPr')[0].set('descr',b['text'])
 cap=doc.add_paragraph(style='Caption');cap.paragraph_format.keep_together=True;cap.add_run(f"Fig. {b['number']}").bold=True;cap.add_run(' '+b['text']);L.highlight(cap,hilite and b.get('rev',False))
def main_doc(path,hilite=False):
 d=L.init_doc();L.par(d,TITLE,'Title')
 L.par(d,'Author names and affiliations to be supplied by the submitting authors')
 pp=L.par(d,'Corresponding author email and ORCIDs pending');pp.paragraph_format.space_after=Pt(7)
 for r in pp.runs:r.font.size=Pt(9.5)
 L.par(d,'Abstract','Heading 1');L.par(d,ABSTRACT,on=hilite)
 L.par(d,'Keywords  antireflection coatings; thickness correlation; robust inverse design; covariance learning; optical fabrication; nonlinear reliability')
 for b in B:
  if b['type']=='p':L.par(d,b['text'],on=hilite and b.get('rev',False))
  elif b['type']=='h':L.par(d,b['text'],'Heading '+str(b['level']))
  elif b['type']=='eq':L.add_eq(d,b['index'],b.get('rev',False),hilite)
  elif b['type']=='table':L.add_table(d,b,hilite)
  elif b['type']=='fig':addfigure(d,b,hilite)
  elif b['type']=='break':d.add_page_break()
  elif b['type']=='algorithm':
   pp=L.par(d,b['title'],'Heading 2')
   for i,line in enumerate(b['lines']):
    pp=L.par(d,line);pp.paragraph_format.left_indent=Inches(.12);pp.paragraph_format.keep_with_next=i<len(b['lines'])-1
  elif b['type']=='ref':
   body,sep,url=b['text'].partition(' https://doi.org/')
   pp=L.par(d,f"[{b['number']}] {body} ");pp.alignment=WD_ALIGN_PARAGRAPH.LEFT;pp.paragraph_format.keep_together=True
   pp.paragraph_format.space_after=Pt(6)
   if sep:link(d,pp,'https://doi.org/'+url.split(' ')[0])
   if '[Conference paper]' in url:pp.add_run(' [Conference paper]')
 remove_break_paragraphs(d);d.save(path)

def remove_break_paragraphs(doc):
 # A page-break-only paragraph can spill onto an otherwise empty page.
 for pp in list(doc.element.body.findall(qn('w:p'))):
  if not pp.xpath('.//w:br[@w:type="page"]'):continue
  nxt=pp.getnext()
  if nxt is not None and nxt.tag==qn('w:p'):
   pr=nxt.find(qn('w:pPr'))
   if pr is None:pr=OxmlElement('w:pPr');nxt.insert(0,pr)
   v=OxmlElement('w:pageBreakBefore');pr.append(v);pp.getparent().remove(pp)

def review_doc():
 d=L.init_doc();L.par(d,'Internal review and revision record','Title')
 L.par(d,TITLE);L.par(d,'Prepared 5 November 2026 for author review. This record is an internal scientific and editorial check, not journal peer review.')
 L.par(d,'Research distinction','Heading 1')
 L.par(d,'This paper changes the physical system and scientific target from the earlier communication manuscripts. It studies planar optical-coating inverse design, deposition-error correlation and nonlinear fabrication yield. It uses characteristic matrices, material dispersion and thickness sensitivities. The earlier visible-light attribution, receiver-orientation calibration, coherent-fiber equalization and quantum-link allocation questions, observations and experiments are not reused. Only generic document-layout helpers were adapted.')
 L.par(d,'Critical review and integrated corrections','Heading 1')
 issues=[
 ('R1 Convergence fairness','The selected sampled-CVaR primary solution reached its iteration budget.','Retained the primary record, continued every selected design with a larger budget and used fresh test draws. SCV converged after 352 more iterations; the yield-tail distinction persisted.','Section 6.6; Table 9'),
 ('R2 Novelty overclaim','Robust coating design, correlated monitoring, statistical margins and CVaR already exist.','Added explicit closest-prior discussion and comparison matrix. The variance identity is treated as established. Contribution is bounded to the executed fixed-marginal comparison and nonlinear diagnostics.','Section 2; Table 1'),
 ('R3 Reliability claim','A Gaussian linearized margin could be mistaken for a nonlinear certificate.','Added its exact sufficient condition and checked feasibility. CE maximum margin is 12.31%, exceeding the 5% target, so no 95%-yield certificate is claimed.','Section 4.3; Table 6'),
 ('R4 Selective reporting','CE has both useful gains and adverse tail behavior.','Retained lower yields than LW and the common-mode 20.06% tail, with paired contrasts and a tail-focused control.','Sections 6.2–6.3; Figures 5–6'),
 ('R5 Distribution shifts','A covariance model assumes zero mean and does not cover heavy tails.','Executed separately frozen mean-bias and Student-t audits with new seeds. Invalid thickness is counted as failure and excluded from optical extrema.','Section 6.6; Figure 9'),
 ('R6 Model and search validity','Absorption, dispersion, grid error and initialization could drive an apparent gain.','Retained complex hafnia loss, documented the silica proxy, checked independent scattering and gradients, refined grids, and reported all optimizer starts.','Sections 3, 5.3, 6.5; Tables 4–6'),
 ('R7 Authorship and AI use','No author approvals, measured data or originality service results were supplied.','Used synthetic-data descriptions, explicit generative-assistance disclosure and pending factual declarations. No acceptance, physical validation or similarity-score claim is made.','Section 5.4; Statements and Declarations')]
 for title,concern,change,where in issues:
  if title.startswith('R4'):d.add_page_break()
  L.par(d,title,'Heading 2');L.par(d,concern);L.par(d,change+' Location: '+where+'.')
 d.add_page_break();L.par(d,'Seven step workflow status','Heading 1')
 for title,t in [
 ('1 Manuscript and journal','Created a new Optical Review research manuscript and supporting simulation package. The publisher instructions were checked on 5 November 2026.'),
 ('2 Critical review','Applied an internal adversarial review covering closest prior art, fairness, nonlinear validity, negative results and author accountability. This is not independent peer review.'),
 ('3 Highlighted revision','Integrated the corrections, added nomenclature and native numbered equations, and created a separate Word copy with substantive review additions highlighted in yellow.'),
 ('4 Additional curves','Added new-seed mean-bias and heavy-tail curves after internal review, plus the optimizer continuation audit. Prespecified correlation, tolerance, witness-count and restart sweeps are identified separately.'),
 ('5 Integrated package','Prepared clean and highlighted Word files, a readable PDF, editable tables and equations, vector figure sources, high-resolution raster figures, raw synthetic records and executable code.'),
 ('6 Originality and AI disclosure','No Turnitin or AI-detector service was accessed and no similarity score is asserted. The prose and diagrams were newly prepared with citations; that is not a plagiarism-service certification. Assistance is disclosed in Methods, as required by the journal. No detector-evasion work was performed.'),
 ('7 Submission preparation','A cover-letter and declarations worksheet is included. Author metadata, independent scientific verification, truthful declarations and a persistent data identifier remain pending. No submission or acceptance claim is made.')]:
  L.par(d,title,'Heading 2');L.par(d,t)
 L.par(d,'Journal format and evidence status','Heading 1')
 L.par(d,'The draft has a 150–250 word abstract, six keywords, decimal section headings, consecutive square-bracket citations, native editable Word equations, numbered editable tables, and embedded figures. Separate EPS and SVG sources and 600 dpi plots are provided; pictorial diagrams are 1200 dpi. Times New Roman is specified in Word; plotted text uses the installed Liberation Serif metric-compatible substitute with STIX math. The submission portal may impose additional title-page or upload requirements.')
 L.par(d,'There are 25 cited publications, 14 from 2024–2026, including one clearly labeled SPIE conference paper. References include the closest statistical, correlated-error and CVaR prior work. DOI records, publisher/author provenance and an access-level matrix are included. Some articles were accessible only through abstracts and metadata; no detailed algorithm or reproduced performance claim is based on unavailable full text.')
 L.par(d,'The current study is reproducible simulation evidence. It does not establish material-specific process capability, physical coating yield, general minimax optimality or novelty priority. The journal editor and reviewers decide whether the scope and contribution merit publication.')
 link(d,L.par(d,'Official author instructions: '),'https://link.springer.com/journal/10043/submission-guidelines')
 remove_break_paragraphs(d);d.save(OUT/'Optical_Review_Coating_Internal_Review.docx')

def cover_doc():
 d=L.init_doc();L.par(d,'Cover letter and author declarations','Title')
 L.par(d,'Draft for completion by the actual authors. Do not submit with unresolved placeholders.')
 L.par(d,'Cover letter','Heading 1')
 L.par(d,'5 November 2026');L.par(d,'Dear Editors of Optical Review,')
 L.par(d,'Please consider our manuscript entitled “'+TITLE+'” as a regular research article.')
 L.par(d,'The study examines how uncertain correlations between layer-thickness errors affect broadband antireflection coating design. Its optical system is an eight-layer silica–hafnia stack on BK7, evaluated over wavelength, angle and polarization. The manuscript compares nominal, local-margin, learned-covariance and sampled-tail-risk objectives with independent nonlinear Monte Carlo testing.')
 L.par(d,'The contribution is a controlled fixed-marginal correlation study and an explicit distinction between specification yield and severe reflection loss. It does not claim that covariance envelopes or robust optical design are new. The retained adverse result is central: a correlation-envelope design improves compliance at a fixed specification yet has a worse common-mode reflection tail. The paper provides independent optical-model checks and complete synthetic inputs, outputs and code.')
 L.par(d,'This contribution concerns optical-system design, materials-based interference modeling and manufacturing uncertainty. It is distinct from our earlier manuscripts on visible-light source–channel attribution and communication-signal processing. [Authors must verify the relationship to any prior submitted or published work and add citations or disclosures where required.]')
 L.par(d,'Generative AI assistance in framing, coding, analysis, drafting and figure preparation is disclosed in the Methods section. [Insert the verified statements on author approval, originality, exclusive submission, prior dissemination, funding, competing interests and repository DOI.]')
 L.par(d,'Sincerely,');sig=L.par(d,'[Corresponding author full name]\n[Institution and postal address]\n[Active email and ORCID]');sig.alignment=WD_ALIGN_PARAGRAPH.LEFT
 d.add_page_break();L.par(d,'Required factual author inputs','Heading 1')
 for title,t in [
 ('Authorship and responsibility','Provide author names, affiliations, author order, ORCIDs, corresponding-author details and genuine contributions. Every author must independently review the mathematics, code, raw outputs, references and conclusions and approve submission.'),
 ('Funding and competing interests','Insert accurate funding, grant numbers and financial or nonfinancial interests. Do not use an unverified statement that no conflicts or funding exist.'),
 ('Originality and prior dissemination','Confirm publication and concurrent-submission status, any preprint and its licence, related manuscripts, overlap and permissions. No similarity-service result is currently available.'),
 ('Data and software availability','Validate the package in an independent environment, select the applicable software/data licence, deposit the approved materials in an appropriate persistent repository and insert its DOI. Third-party CC0 material data retain provenance.'),
 ('Scientific validation','Decide whether simulation-only evidence is adequate for the claimed contribution. If measurements are added, report the actual instrument, sample, process and error data and rerun analysis; do not label these simulations experimental.'),
 ('Journal submission','Recheck current portal requirements and publication conditions. Upload the approved editable manuscript, separate figure sources, supplementary information and declarations. Acceptance cannot be promised.')]:
  L.par(d,title,'Heading 2');L.par(d,t)
 remove_break_paragraphs(d);d.save(OUT/'Optical_Review_Coating_Cover_and_Declarations.docx')

if __name__=='__main__':
 OUT.mkdir(exist_ok=True);prepare_math()
 main_doc(OUT/'Optical_Review_Coating_Manuscript.docx')
 main_doc(OUT/'Optical_Review_Coating_Highlighted.docx',True)
 review_doc();cover_doc()
 (ROOT/'notes/manuscript_blocks.json').write_text(json.dumps(dict(title=TITLE,abstract=ABSTRACT,equations=EQS,blocks=B),ensure_ascii=False,indent=2))
 print('Abstract words',len(ABSTRACT.split()),'equations',len(EQS),'figures',sum(b['type']=='fig' for b in B),'tables',sum(b['type']=='table' for b in B),'references',len(order))
