# hard00_steps3 — accepted trajectory plan

**View identification & dimension chains**

- **Top (XY from +Z):** rectangle split by two interior lines into three X-sections. No overall X dim — chain: 28 + 21 + 17 = **66 mm**. Y depth given as overall: **36 mm**.
- **Front (XZ from −Y):** staircase profile, tallest section at the left (low X), stepping down toward +X. X chain repeated: 28 + 21 + 17 = 66. Z chain (no overall given): 10 + 13 + 15 = **38 mm**. Step levels: z=10 (top of low section, X 49–66), z=23 (top of middle section, X 28–49), z=38 (top of tall section, X 0–28).
- **Right (YZ from +X):** 36 wide × 38 tall rectangle with *solid* horizontal lines at z=10 and z=23 — confirms the shortest step (17 wide) is nearest the +X viewer, so the profile ascends toward low X. Confirms Y=36 and Z chain 10+13+15=38.
- **ISO:** plain 3-step staircase, constant depth — consistent, no extra features.

**Feature list** (no holes, no fillets/chamfers):
1. Bottom tier: 66 × 36 × 10 (full footprint, z 0→10)
2. Middle tier: (28+21)=49 × 36 × 13 (X 0→49, z 10→23)
3. Top tier: 28 × 36 × 15 (X 0→28, z 23→38)

Overall: 66 (X) × 36 (Y) × 38 (Z).

---

Reading is unchanged: a 3-step staircase, overall 66 (X = 28+21+17) × 36 (Y) × 38 (Z = 10+13+15). The failure was purely an API issue: `with BuildPart() as part:` binds `part` to the *builder*, not the solid. Fix: build under a builder name (`bp`), then bind the finished solid with `part = bp.part` before exporting.