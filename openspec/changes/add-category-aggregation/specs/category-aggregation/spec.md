# Category Aggregation Specification

## ADDED Requirements

### Requirement: CES Aggregation

The system SHALL aggregate amenity accessibility within categories using Constant Elasticity of Substitution (CES).

#### Scenario: CES formula implementation

- **WHEN** aggregating amenities within category c
- **THEN** aggregate value SHALL be: V_c = (Σ(w_ia * Q_a)^ρ_c)^(1/ρ_c)
- **AND** ρ_c SHALL be category-specific elasticity parameter
- **AND** ρ_c SHALL be in range (-∞, 1), typically [0, 0.9]

#### Scenario: Perfect substitutes (ρ → 1)

- **WHEN** ρ_c approaches 1
- **THEN** CES SHALL approach linear sum (amenities are perfect substitutes)

#### Scenario: Cobb-Douglas case (ρ → 0)

- **WHEN** ρ_c approaches 0
- **THEN** CES SHALL approach geometric mean

---

### Requirement: Satiation Curves

The system SHALL model diminishing returns via satiation curves.

#### Scenario: Satiation formula

- **WHEN** computing category subscore
- **THEN** satiation SHALL be: S_c = 100 · (1 - exp(-κ_c · V_c))
- **AND** κ_c SHALL control satiation rate
- **AND** S_c SHALL asymptote to 100 as V_c increases

#### Scenario: Anchor-based κ computation

- **WHEN** computing κ_c
- **THEN** κ_c = -ln(1 - S_anchor/100) / V_anchor
- **AND** anchor SHALL be defined per category (e.g., 5 groceries → 80 points)
- **AND** κ_c SHALL be validated > 0

---

### Requirement: Diversity Bonuses

The system SHALL reward within-category diversity.

#### Scenario: Shannon diversity

- **WHEN** computing diversity bonus
- **THEN** Shannon index SHALL be computed: H = -Σ(p_i · ln(p_i))
- **AND** p_i SHALL be proportion of subcategory i
- **AND** higher diversity SHALL increase score (1.0-1.2× multiplier)
