## MODIFIED Requirements

### Requirement: CES Aggregation within Essential Categories

The system SHALL aggregate amenity accessibility within each essential category using CES (Constant Elasticity of Substitution) with elasticity ρ_c.

#### Scenario: Compute CES for grocery category
- **WHEN** a hex has 5 grocery stores with varying Q_a and w_{i,a} values
- **THEN** the system SHALL compute z_{i,a} = (Q_a · w_{i,a})^ρ_c for each, then V_grocery = (Σ z_{i,a})^(1/ρ_c)

#### Scenario: Handle empty categories
- **WHEN** a hex has zero amenities in a category (e.g., no pharmacies)
- **THEN** V_c SHALL be 0 for that category

#### Scenario: Elasticity parameter variation
- **WHEN** ρ_c = 0.65 (default for essentials)
- **THEN** the CES SHALL exhibit moderate substitution (between Cobb-Douglas and perfect substitutes)

#### Scenario: Numeric inputs coerced to float
- **WHEN** the CES kernel receives numpy arrays or pandas Series containing numeric quality and accessibility values
- **THEN** the system SHALL coerce those inputs to float64 before applying the JIT-compiled computation so that aggregation proceeds without dtype errors
