# Phase 26 — Private iOS App Distribution

This guide explains how to install and run the app privately on iPhone using either direct sideloading from Xcode or Apple TestFlight.

---

## Prerequisites

- A working iOS app target in Xcode (`iOS 16+` for this project).
- A unique Bundle Identifier (example: `com.yourcompany.metabolicintelligence`).
- Apple ID signed in to Xcode.
- Physical iPhone (for direct sideload) or testers invited in App Store Connect (for TestFlight).

---

## Option 1: Direct Sideload (Mac required)

Use this when you want to run privately on your own device quickly.

### 1) Install Xcode

1. Install the latest stable Xcode from the Mac App Store.
2. Open Xcode once and accept the license.
3. Install required components when prompted.

### 2) Connect iPhone

1. Connect your iPhone via USB (or configure wireless debugging later).
2. On iPhone, tap **Trust This Computer**.
3. In Xcode, open **Window → Devices and Simulators** and confirm the phone appears.

### 3) Select development team

1. Open the iOS project/workspace in Xcode.
2. Select the app target.
3. Go to **Signing & Capabilities**.
4. Enable **Automatically manage signing**.
5. Select your Apple Team.
6. Ensure Bundle Identifier is unique.

### 4) Build & Run

1. Select your iPhone as the run destination.
2. Press **⌘R** (Run).
3. Wait for Xcode to build, sign, install, and launch.

### 5) Trust developer certificate (first run)

If iOS blocks launch:

1. On iPhone: **Settings → General → VPN & Device Management**.
2. Under *Developer App*, select your Apple ID certificate.
3. Tap **Trust**.
4. Launch app again.

### Direct sideload notes

- With a free Apple account, apps can expire quickly and may need re-sign/install.
- Paid Apple Developer membership gives more stable provisioning behavior.

---

## Option 2: TestFlight (recommended)

Use this for repeat private distribution to teammates, QA, or stakeholders.

### 1) Enroll in Apple Developer Program

1. Join Apple Developer Program (paid membership).
2. Wait for enrollment to become active.

### 2) Create App ID

1. In Apple Developer portal, create an App ID for your bundle ID.
2. Enable capabilities your app needs (example: Push Notifications, HealthKit where applicable).

### 3) Configure App Store Connect

1. In App Store Connect, create a new app record.
2. Match the app’s Bundle ID exactly.
3. Fill basic app metadata (name, platform, primary language).

### 4) Upload build via Xcode

1. In Xcode, set version/build number.
2. Choose **Product → Archive**.
3. In Organizer, choose archive → **Distribute App**.
4. Select **App Store Connect → Upload**.
5. Complete signing and upload flow.

### 5) Create internal testing group

1. In App Store Connect → TestFlight.
2. Add internal testers (users in your App Store Connect team).
3. Assign the uploaded build to the internal group.

### 6) Install via TestFlight

1. Testers install **TestFlight** app on iPhone.
2. Accept invite email or public link (if configured).
3. Install and launch build through TestFlight.

### TestFlight notes

- Internal testers usually get access quickly after processing.
- External testers require Apple Beta App Review before distribution.
- TestFlight builds expire after a period; upload a new build to continue testing.

---

## Certificate management explained

### Signing certificates

A signing certificate proves who built the app.

- **Development certificate**: used for local debugging and device installs from Xcode.
- **Distribution certificate**: used for TestFlight/App Store style distribution.

Xcode can usually manage these automatically when “Automatically manage signing” is enabled.

### Provisioning profiles

A provisioning profile links:

1. App ID (Bundle Identifier)
2. Certificate(s)
3. Allowed devices (for development/ad hoc)
4. Entitlements/capabilities

If any part mismatches (wrong bundle ID, wrong cert, missing capability), build/install fails.

### Bundle identifiers

The Bundle ID is the app’s unique identity in Apple’s ecosystem.

Rules:

- Must be globally unique for your team.
- Must match in Xcode target and App Store Connect record.
- Should stay stable once released to testers/users.

---

## Windows limitation (important)

iOS apps must be compiled and signed with Apple tooling on macOS.

- You can edit code on Windows.
- Final build/sign/upload requires macOS + Xcode.

Workarounds:

- Use a Mac directly.
- Use a CI/CD pipeline running on macOS runners.
- Use a cloud macOS service for build/sign workflows.

---

## Screenshot descriptions (what users should see)

Use these checkpoints while following setup:

1. **Xcode Signing & Capabilities screen**
   - Shows team selected and “Automatically manage signing” enabled.
2. **Xcode Run destination**
   - Physical iPhone visible as active target.
3. **Xcode Organizer archive upload success**
   - Confirms build uploaded to App Store Connect.
4. **App Store Connect TestFlight build page**
   - Build processed and assigned to internal testing group.
5. **iPhone TestFlight install screen**
   - App card with “Install” or “Open” button.
6. **iPhone VPN & Device Management trust screen** (direct sideload path)
   - Developer certificate trust option visible.

---

## Common errors and fixes

### 1) “No signing certificate found”

**Cause**: Xcode cannot find/create a valid signing identity.

**Fix**:

- Xcode → Settings → Accounts: re-login Apple ID.
- In target Signing settings, re-select Team.
- Toggle “Automatically manage signing” off/on.

### 2) “Bundle identifier is already in use”

**Cause**: Bundle ID not unique for your team.

**Fix**:

- Change Bundle Identifier to a unique reverse-domain value.
- Update App ID and App Store Connect app record accordingly.

### 3) “Provisioning profile doesn’t include device”

**Cause**: Device UDID missing from profile (manual signing path).

**Fix**:

- Add the device in Apple Developer portal.
- Regenerate profile, download/install, rebuild.
- Prefer automatic signing if possible.

### 4) App installs but won’t open on device (untrusted developer)

**Cause**: Developer certificate not trusted on iPhone.

**Fix**:

- iPhone: **Settings → General → VPN & Device Management → Trust Developer App**.

### 5) TestFlight build not appearing

**Cause**: Build still processing, wrong bundle/version, or not assigned to tester group.

**Fix**:

- Wait for processing to finish.
- Confirm bundle ID and build number are correct.
- Assign build to internal testing group explicitly.

### 6) “Missing entitlement” or capability-related signing errors

**Cause**: Capability enabled in project but not in App ID/profile.

**Fix**:

- Enable same capability in Apple Developer portal.
- Regenerate signing assets (or let Xcode auto-manage).
- Clean build folder and rebuild.

### 7) Upload failed from Organizer

**Cause**: Versioning/signing/metadata issues.

**Fix**:

- Increment build number.
- Validate archive before upload.
- Re-check certificate/profile status in Signing settings.

---

## Recommended rollout sequence

1. Validate locally with **Direct Sideload** on 1–2 internal devices.
2. Move to **TestFlight internal testing** for broader private testing.
3. Automate archive/upload in macOS CI once release cadence increases.
