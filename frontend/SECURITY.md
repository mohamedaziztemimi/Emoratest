# Security Policy

## LGPL License Findings - Accepted Risk (False Positive)

### Issue: `@img/sharp-libvips-*` packages (LGPL-3.0-or-later)

**Status**: ACCEPTED - Not a security or legal risk

**Explanation**:
These are optional, platform-specific native binary dependencies for the `sharp` image processing library, used internally by Next.js for Image Optimization.

**Why this is NOT a security or legal risk:**

1. **LGPL v3 allows dynamic linking**: These libraries are dynamically loaded at runtime. LGPL v3 explicitly permits dynamic linking without requiring derivative works to be open source. The copyleft effect only applies to static linking or modifying the library itself.

2. **Indirect dependency**: EmoraTest application code does not directly link to these libraries. The dependency chain is:
   - Next.js → sharp → @img/sharp-libvips-* (optional)

3. **Platform-specific**: These packages only install on matching platforms (darwin-x64, linux-arm64, etc.). They are NOT installed in all environments.

4. **Optional**: Marked as `optional: true` - sharp falls back to its built-in binaries if unavailable.

5. **No user data exposure**: These libraries process images locally and do not transmit any data externally.

**Security scanners may flag this because:**
- Static analysis sees LGPL license and assumes worst-case copyleft impact
- Scanners don't understand that dynamic linking is permitted under LGPL
- Scanners don't distinguish between optional and required dependencies

**Legal Opinion**:
Using LGPL v3 libraries via dynamic linking does NOT require releasing your application source code. This is a well-understood and accepted interpretation of LGPL v3.

---

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email security@emoratest.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We will respond within 48 hours and provide a timeline for resolution.
