# essentials-access Specification

## Purpose
TBD - created by archiving change add-essentials-access. Update Purpose after archive.
## Requirements
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

### Requirement: Satiation Curve Application

The system SHALL apply satiation curves to prevent unbounded returns from many similar amenities.

#### Scenario: Map CES to 0-100 scale with satiation

- **WHEN** V_c is computed for a category
- **THEN** the system SHALL compute S_c = 100 · (1 - exp(-κ_c · V_c)) per equation E12

#### Scenario: Anchor-based calibration

- **WHEN** satiation mode is "anchor" with S_target=75 at V_target (3 solid options)
- **THEN** κ_c SHALL be computed as -ln(1 - S_target/100) / V_target

#### Scenario: Asymptotic ceiling

- **WHEN** V_c grows very large
- **THEN** S_c SHALL approach but never exceed 100

### Requirement: Within-Category Diversity Bonus

The system SHALL reward diversity of amenity types within each essential category.

#### Scenario: Compute Shannon entropy for diversity

- **WHEN** a category has multiple subtypes (e.g., supermarket, ethnic grocery, farmers market)
- **THEN** the system SHALL compute H_c = -Σ p_{c,g} ln(p_{c,g}) where p = Q-weighted shares

#### Scenario: Apply diversity bonus

- **WHEN** H_c is computed
- **THEN** the system SHALL add DivBonus_c = υ_c · (e^H_c - 1), capped at 5 points per category

#### Scenario: Single-subtype category

- **WHEN** all amenities in a category are the same subtype
- **THEN** H_c = 0 and DivBonus_c = 0

### Requirement: Shortfall Penalty for Missing Essentials

The system SHALL penalize hexes that lack adequate access to critical essential categories.

#### Scenario: Identify shortfall categories

- **WHEN** a category score S_c < S_min (default 20 points)
- **THEN** the system SHALL count it as a shortfall

#### Scenario: Apply per-category penalty

- **WHEN** N categories are in shortfall
- **THEN** the system SHALL subtract min(P_max, N · P_per_miss) points from EA

#### Scenario: Cap penalty

- **WHEN** many categories are in shortfall
- **THEN** the total penalty SHALL NOT exceed P_max (default 8 points)

### Requirement: EA Subscore Composition

The system SHALL compute the final Essentials Access score as the mean of category scores minus shortfall penalty.

#### Scenario: Aggregate essential categories

- **WHEN** all 7 essential categories (grocery, pharmacy, primary_care, childcare, K8_school, bank_atm, postal_parcel) are scored
- **THEN** the system SHALL compute EA = (1/7) · Σ (S_c + DivBonus_c) - ShortfallPenalty per equation E14-E15

#### Scenario: EA output range

- **WHEN** EA is computed
- **THEN** the value SHALL be in the range [0, 100] (floor at 0 if penalty exceeds base score)

### Requirement: EA Explainability

The system SHALL provide per-hex attribution showing which POIs and categories drive EA scores.

#### Scenario: Identify top contributing POIs per category

- **WHEN** computing EA for a hex
- **THEN** the system SHALL record the top 3 POIs per essential category ranked by z_{i,a}

#### Scenario: Store category-level contributions

- **WHEN** EA is computed
- **THEN** the output SHALL include individual S_c scores and diversity bonuses per category

#### Scenario: Flag shortfall categories

- **WHEN** categories are in shortfall
- **THEN** the output SHALL list which categories triggered the penalty

### Requirement: EA Data Quality Validation

The system SHALL validate EA scores against expected distributions and invariants.

#### Scenario: Range validation

- **WHEN** EA scores are written
- **THEN** all values SHALL be >= 0 and <= 100

#### Scenario: Monotonicity check

- **WHEN** a hex has strictly more/better accessible amenities than another
- **THEN** its EA score SHALL be greater than or equal (holding parameters constant)

#### Scenario: Detect anomalies

- **WHEN** EA distribution has unexpected patterns (e.g., excessive zeros, ceiling clustering)
- **THEN** the system SHALL log warnings for manual review

