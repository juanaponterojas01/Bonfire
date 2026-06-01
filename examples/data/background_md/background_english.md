# John Smith

**Email:** john.smith@example.com  
**Phone:** +1 (555) 123-4567  
**Address:** 742 Maple Avenue, Apt 3B, Cambridge, MA 02139, USA  
**LinkedIn:** linkedin.com/in/johnsmith-mech

---

## Education

### Master of Science in Mechanical Engineering
**Massachusetts Institute of Technology (MIT), Cambridge, MA, USA** — *Sep 2021 – Jun 2023*

- **GPA:** 3.9 / 4.0
- **Thesis:** "Optimization of Vertical-Axis Wind Turbine Arrays Using Actuator-Line CFD Simulations"
- **Relevant Subjects:** Computational Fluid Dynamics, Turbomachinery, Renewable Energy Systems, Finite Element Methods, Advanced Thermodynamics, Control Systems, Numerical Methods for PDEs
- **Research Focus:** CFD modeling of wake interactions in distributed wind energy systems
- **Awards:** MIT Energy Fellowship (2022–2023)

### Bachelor of Science in Mechanical Engineering
**University of Michigan, Ann Arbor, MI, USA** — *Sep 2016 – May 2020*

- **GPA:** 3.7 / 4.0
- **Relevant Subjects:** Fluid Mechanics, Thermodynamics, Heat Transfer, Solid Mechanics, Dynamics, Machine Design, MATLAB Programming, Engineering Statistics
- **Senior Capstone:** "Design of a Low-Cost Solar-Powered Water Pump for Rural Communities"
- **Dean's List:** Fall 2017, Spring 2018, Fall 2019

---

## Experience

### Graduate Research Assistant — MIT Renewable Energy CFD Lab
**Cambridge, MA, USA** — *Sep 2022 – Jun 2023*

- Developed high-fidelity actuator-line CFD models of vertical-axis wind turbines (VAWTs) using ANSYS Fluent with user-defined functions (UDFs) written in C.
- Simulated and analyzed wake interaction effects in small wind turbine arrays of up to 12 turbines, achieving a 15% improvement in array power density through optimized staggered layouts.
- Automated parametric sweep workflows using MATLAB and Python scripts, reducing simulation setup time by 40%.
- Presented findings at the 2023 ASME Turbo Expo in Boston, MA.
- Published co-authored paper in *Renewable Energy* journal (2023): "Wake Steering for Vertical-Axis Wind Turbines in Close Proximity."

### CFD Engineering Intern — Siemens Energy
**Orlando, FL, USA** — *Jun 2022 – Aug 2022*

- Performed steady-state and transient CFD simulations of gas turbine cooling channels using ANSYS Fluent and CFX.
- Validated simulation results against experimental thermocouple data, achieving less than 5% average deviation.
- Created automated meshing scripts in ANSYS Meshing Workbench, cutting mesh generation time by 30%.
- Documented standard operating procedures for internal CFD validation workflows.

### Mechanical Design Intern — Vestas Wind Systems
**Portland, OR, USA** — *Jun 2020 – Aug 2020*

- Assisted in the structural analysis of wind turbine nacelle components using ANSYS Mechanical APDL.
- Conducted fatigue life assessments of bolted flange connections under dynamic loading conditions.
- Designed and drafted 3D CAD models of drivetrain sub-assemblies in SolidWorks, supporting the senior design review team.
- Compiled technical reports on bolt preload optimization for the Nacelle Design Department.

---

## Skills

| Category | Skill | Proficiency | Years of Experience |
|---|---|---|---|
| **Engineering Software** | ANSYS Fluent | Expert | 4 |
| | ANSYS CFX | Advanced | 2 |
| | ANSYS Mechanical APDL | Intermediate | 2 |
| | ANSYS Meshing | Advanced | 3 |
| | SolidWorks | Advanced | 4 |
| | AutoCAD | Intermediate | 2 |
| **Programming & Scripting** | Python | Advanced | 4 |
| | MATLAB | Advanced | 5 |
| | C (UDFs) | Intermediate | 2 |
| | Bash / Shell Scripting | Intermediate | 2 |
| **CFD & Simulation** | RANS / URANS Turbulence Modeling | Advanced | 3 |
| | Actuator-Line / Actuator-Disk Methods | Advanced | 2 |
| | Conjugate Heat Transfer | Intermediate | 1 |
| | Mesh Generation & Optimization | Advanced | 3 |
| **Tools & Platforms** | Git / GitHub | Advanced | 3 |
| | Linux / HPC Clusters | Advanced | 3 |
| | LaTeX | Advanced | 4 |
| | Microsoft Office Suite | Expert | 6 |
| **Languages** | English | Native | — |
| | German | Intermediate (B1) | — |

---

## Projects

### 1. VAWT Array Wake Optimization (Master's Thesis)
**Duration:** Sep 2022 – Jun 2023  
**Role:** Lead Researcher  
**Technologies:** ANSYS Fluent, MATLAB, Python, C (UDFs), HPC Cluster (SLURM)

Developed actuator-line CFD models for vertical-axis wind turbines to study wake interactions in closely spaced arrays. The project involved:
- Implementing a custom actuator-line forcing term via ANSYS Fluent user-defined functions in C.
- Validating single-turbine wake profiles against published wind tunnel data.
- Running over 200 parametric LES simulations on a 256-core HPC cluster to explore array layouts.
- Applying genetic algorithm optimization in MATLAB to identify optimal turbine spacing and arrangement.

**Outcome:** Achieved 15% higher power density compared to baseline aligned configurations. Results published in *Renewable Energy* (2023).

### 2. Solar-Powered Water Pump for Rural Communities (B.Sc. Capstone)
**Duration:** Jan 2020 – May 2020  
**Role:** Mechanical Design Lead  
**Technologies:** SolidWorks, MATLAB, ANSYS Mechanical

Designed a low-cost, solar-powered centrifugal water pump for off-grid communities in sub-Saharan Africa. The team of four:
- Sized the photovoltaic array and motor-pump assembly based on estimated daily water demand (5,000 L/day).
- Performed structural FEA in ANSYS Mechanical on the pump housing under static pressure loads.
- Optimized the impeller geometry using MATLAB-based blade element momentum theory.
- Built and tested a functional 1:2 scale prototype at the Michigan Engineering Lab.

**Outcome:** Final design achieved a flow rate of 35 L/min at 10 m head with 60% overall system efficiency. Estimated unit cost under $150.

### 3. CFD Validation of Gas Turbine Cooling Channels (Siemens Energy Internship Project)
**Duration:** Jun 2022 – Aug 2022  
**Role:** CFD Engineer Intern  
**Technologies:** ANSYS Fluent, ANSYS CFX, ANSYS Meshing, Python, MATLAB

Conducted a validation study of conjugate heat transfer in internally cooled turbine blades:
- Built structured multi-block meshes of serpentine cooling passages (~5 million cells).
- Ran steady RANS simulations (k-omega SST turbulence model) at engine-representative Reynolds numbers.
- Compared predicted metal temperatures against experimental thermocouple measurements from the Siemens Energy test rig.
- Performed a mesh sensitivity study with three mesh densities to quantify discretization error.

**Outcome:** Predicted temperatures within 5% of experimental data. Developed a validated meshing and simulation protocol now used by the Siemens Energy cooling design team.

### 4. Open-Source Wind Turbine Performance Analyzer (Personal Project)
**Duration:** Oct 2023 – Present  
**Role:** Sole Developer  
**Technologies:** Python, NumPy, Pandas, Matplotlib, Flask, Git, CI/CD (GitHub Actions)

Building a web-based tool for rapid performance assessment of small wind turbines:
- Backend Python module for BEM (Blade Element Momentum) calculations with customizable airfoil data.
- REST API built with Flask to serve performance curves (power vs. wind speed, Cp vs. TSR).
- Interactive front-end for uploading turbine geometry and visualizing results.
- Unit-tested with pytest; CI pipeline runs on every push via GitHub Actions.

**Outcome:** Repository public on GitHub with 30+ stars. Used by two graduate students at MIT for preliminary turbine design studies.
