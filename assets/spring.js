/* Pružina podľa Apple (WWDC „Designing Fluid Interfaces“): parametre damping (pomer tlmenia, 1 = bez prekmitu)
   a response (sekundy, ako rýchlo dosiahne cieľ). Je prerušiteľná: nový cieľ pokračuje z aktuálnej hodnoty
   aj rýchlosti, takže pohyb sa dá kedykoľvek otočiť bez skoku. Používajú ju hlavná stránka aj ukážky. */
(function (w) {
  'use strict';
  var H = 1 / 240;                                    // krok integrácie

  function Spring(value, o) {
    o = o || {};
    this.x = value; this.v = 0; this.target = value;
    this.eps = o.eps || 0.001;                        // pokoj: vzdialenosť od cieľa (v jednotkách hodnoty)
    this.raf = 0; this.last = 0;
    this.onUpdate = null; this.onRest = null;
    this.params(o.response || 0.4, o.damping == null ? 1 : o.damping);
  }
  Spring.prototype.params = function (response, damping) {
    var w0 = 2 * Math.PI / response;                 // stiffness = (2π/response)², damping = 4π·ζ/response
    this.response = response; this.damping = damping;
    this.k = w0 * w0; this.c = 2 * damping * w0;
    return this;
  };
  Spring.prototype.to = function (target, o) {
    o = o || {};
    if (o.response || o.damping != null) this.params(o.response || this.response, o.damping == null ? this.damping : o.damping);
    if (o.velocity != null) this.v = o.velocity;
    this.target = target;
    this.onRest = o.onRest || null;
    if (!this.raf) {
      var s = this;
      this.last = 0;
      this.raf = requestAnimationFrame(function f(t) { s.step(t, f); });
    }
    return this;
  };
  Spring.prototype.step = function (t, f) {
    var dt = this.last ? Math.min(0.05, (t - this.last) / 1000) : 1 / 60;
    this.last = t;
    for (var n = Math.max(1, Math.round(dt / H)), h = dt / n, i = 0; i < n; i++) {
      var a = -this.k * (this.x - this.target) - this.c * this.v;
      this.v += a * h; this.x += this.v * h;
    }
    if (Math.abs(this.x - this.target) < this.eps && Math.abs(this.v) < this.eps * 12) {
      this.x = this.target; this.v = 0; this.raf = 0;
      if (this.onUpdate) this.onUpdate(this.x);
      var r = this.onRest; this.onRest = null;
      if (r) r(this.x);
      return;
    }
    if (this.onUpdate) this.onUpdate(this.x);
    this.raf = requestAnimationFrame(f);
  };
  Spring.prototype.set = function (x) {
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0; this.x = this.target = x; this.v = 0; this.onRest = null;
    if (this.onUpdate) this.onUpdate(x);
    return this;
  };
  Spring.prototype.moving = function () { return !!this.raf; };

  /* Kam by prvok dobehol po švihnutí (Apple: exponenciálne spomalenie ako pri skrolovaní). */
  Spring.project = function (velocity, rate) { rate = rate || 0.998; return velocity / 1000 * rate / (1 - rate); };
  /* Mäkká hranica: čím ďalej za okraj, tým menej prvok nasleduje prst. */
  Spring.rubber = function (over, dim, c) { c = c || 0.55; return over * dim * c / (dim + c * Math.abs(over)); };
  /* Rýchlosť prsta z posledných ~100 ms pohybu (px/s). */
  Spring.Tracker = function () { this.s = []; };
  Spring.Tracker.prototype.reset = function () { this.s = []; };
  Spring.Tracker.prototype.add = function (x) {
    var t = performance.now(); this.s.push([t, x]);
    while (this.s.length > 2 && t - this.s[0][0] > 100) this.s.shift();
  };
  Spring.Tracker.prototype.velocity = function () {
    var s = this.s; if (s.length < 2) return 0;
    var a = s[0], b = s[s.length - 1], dt = (b[0] - a[0]) / 1000;
    if (dt <= 0 || performance.now() - b[0] > 80) return 0;
    return (b[1] - a[1]) / dt;
  };
  Spring.reduced = function () { return w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches; };

  w.Spring = Spring;
})(window);
