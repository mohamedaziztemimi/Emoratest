# Security Policy

## LGPL License Findings - False Positives

### Issue: `@img/sharp-libvips-*` packages (LGPL-3.0-or-later)

**Status**: ACCEPTABLE - False Positive

**Explanation**:
These are optional native binary dependencies for the `sharp` image processing library, which is used internally by Next.js for Image Optimization.

1. **LGPL v3 allows dynamic linking**: These libraries are dynamically loaded at runtime, which LGPL v3 explicitly permits without requiring derivative works to be open source.

2. **Optional dependencies**: These packages are marked as `optional: true` in `package-lock.json` and are platform-specific (darwin-x64, linux-arm64, win32-x64, etc.).

3. **No direct linking**: EmoraTest application code does not directly link to these libraries. They are loaded internally by:
   - Next.js → sharp → @img/sharp-libvips-*

4. **Falls back gracefully**: If these optional binaries are not available, sharp falls back to its own built-in binaries or the serverless prebuilt binaries.

**Legal Assessment**:
- Using LGPL v3 libraries via dynamic linking does **not** require releasing your application source code
- The copyleft effect of LGPL v3 only applies to **static linking** or **modifying the library itself**
- Our use case is purely dynamic runtime loading

**References**:
- [LGPL v3 FAQ - Dynamic Linking](https://www.gnu.org/licenses/lgpl-faq.html)
- [Sharp License Documentation](https://github.com/lovell/sharp/blob/main/LICENSE)

---

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email security@emoratest.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We will respond within 48 hours and provide a timeline for resolution.
