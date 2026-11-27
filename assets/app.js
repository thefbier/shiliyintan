(function () {
  'use strict';

  var state = { data: null, activeCategory: '全部', community: null, activeExchange: 'offers', host: null };

  function el(id) { return document.getElementById(id); }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function renderSite(data) {
    var s = data.site || {};
    el('siteName').textContent = s.name || '十里银滩生活站';
    el('siteDomain').textContent = s.domain || '';
    el('heroTagline').textContent = s.tagline || '';
    el('siteDescription').textContent = s.description || '';
    el('siteUpdated').textContent = s.updated || '';
    el('aboutNotice').textContent = s.notice || '';
    el('footerName').textContent = s.name || '';
    el('footerDomain').textContent = s.domain || '';
    document.title = (s.name || '十里银滩生活站') + ' · ' + (s.domain || '');

    el('quickLinks').innerHTML = (data.quickLinks || []).map(function (item) {
      return '<a href="' + escapeHtml(item.href || '#') + '"><span class="dot"></span>' +
        escapeHtml(item.label || '') + '</a>';
    }).join('');

    el('stats').innerHTML = (data.stats || []).map(function (item) {
      return '<div class="stat"><span class="v">' + escapeHtml(item.value || '') +
        '</span><span class="l">' + escapeHtml(item.label || '') + '</span></div>';
    }).join('');

    renderFilters(data.posts || []);
    renderPosts();
    renderBusinesses(data.businesses || []);
    renderListings(data.listings || []);
    renderCommunity();
    renderHost();
  }

  function renderFilters(posts) {
    var cats = ['全部'];
    posts.forEach(function (p) { if (p.category && cats.indexOf(p.category) < 0) cats.push(p.category); });
    el('postFilters').innerHTML = cats.map(function (cat) {
      return '<button type="button" class="filter' + (cat === state.activeCategory ? ' active' : '') +
        '" data-cat="' + escapeHtml(cat) + '">' + escapeHtml(cat) + '</button>';
    }).join('');
    Array.prototype.forEach.call(el('postFilters').querySelectorAll('.filter'), function (btn) {
      btn.addEventListener('click', function () {
        state.activeCategory = btn.getAttribute('data-cat');
        renderFilters(state.data.posts || []);
        renderPosts();
      });
    });
  }

  function renderPosts() {
    var posts = (state.data.posts || []).filter(function (p) {
      return state.activeCategory === '全部' || p.category === state.activeCategory;
    });
    el('postGrid').innerHTML = posts.map(function (p) {
      var body = (p.sections || []).map(function (sec) {
        return '<h4>' + escapeHtml(sec.heading || '') + '</h4><p>' +
          escapeHtml(sec.text || '') + '</p>';
      }).join('');
      var tags = (p.tags || []).map(function (t) {
        return '<span class="tag">#' + escapeHtml(t) + '</span>';
      }).join('');
      return '<article class="post" data-id="' + escapeHtml(p.id || '') + '">' +
        '<div class="post-meta"><span class="chip">' + escapeHtml(p.category || '') + '</span>' +
        '<span>' + escapeHtml(p.date || '') + '</span></div>' +
        '<h3>' + escapeHtml(p.title || '') + '</h3>' +
        '<p class="excerpt">' + escapeHtml(p.excerpt || '') + '</p>' +
        '<div class="tags">' + tags + '</div>' +
        '<div class="post-body">' + body + '</div>' +
        '<p class="more">展开全文 ↓</p>' +
        '</article>';
    }).join('');

    Array.prototype.forEach.call(el('postGrid').querySelectorAll('.post'), function (card) {
      card.addEventListener('click', function () {
        var open = card.classList.toggle('open');
        var more = card.querySelector('.more');
        if (more) more.textContent = open ? '收起 ↑' : '展开全文 ↓';
      });
    });
  }

  function renderBusinesses(items) {
    var meta = state.bizMeta || {};
    var intro = meta.meta ? '<div class="biz-intro"><strong>' + escapeHtml(meta.meta.title || '商家目录') +
      '</strong><span>核查 ' + escapeHtml(meta.meta.compiledOn || '') + ' · 全部条目待现场核验</span></div>' : '';
    var cards = items.map(function (b) {
      var tags = (b.tags || []).map(function (t) {
        return '<span class="tag">' + escapeHtml(t) + '</span>';
      }).join('');
      var grade = b.grade ? '<span class="grade grade-' + escapeHtml(b.grade) + '" title="信源等级 ' +
        escapeHtml(b.grade) + '">信源 ' + escapeHtml(b.grade) + '</span>' : '';
      var hours = b.hours ? '<span>时间 ' + escapeHtml(b.hours) + '</span>' : '';
      var phone = b.phone ? '<span>联系 ' + escapeHtml(b.phone) + '</span>' : '';
      var source = b.source ? '<div class="biz-source">信源：' + escapeHtml(b.source) +
        (b.verifiedOn ? ' · 核于 ' + escapeHtml(b.verifiedOn) : '') + '</div>' : '';
      return '<article class="biz"><div class="biz-head"><h3>' + escapeHtml(b.name || '') +
        '</h3><span class="area">' + escapeHtml(b.area || '') + '</span></div>' +
        (grade ? '<div class="biz-flags">' + grade + '</div>' : '') +
        '<p>' + escapeHtml(b.desc || '') + '</p>' +
        '<div class="tags">' + tags + '</div>' +
        '<div class="biz-meta">' + hours + phone + '</div>' + source + '</article>';
    }).join('');
    el('bizGrid').innerHTML = intro + cards;
  }

  function renderListings(items) {
    el('listGrid').innerHTML = items.map(function (l) {
      return '<article class="listing"><h3>' + escapeHtml(l.title || '') + '</h3>' +
        '<div class="price">' + escapeHtml(l.price || '价格面议') + '</div>' +
        '<div class="row"><span>' + escapeHtml(l.type || '') + '</span><span>' +
        escapeHtml(l.area || '') + '</span></div>' +
        '<div class="row"><span>更新 ' + escapeHtml(l.date || '') + '</span></div>' +
        '<div class="note">' + escapeHtml(l.note || '') + '</div></article>';
    }).join('');
  }

  // ============ 关系交换机 / 立场专栏 / 社区活动 ============
  function applyTemplate(tpl, name) {
    return String(tpl || '').replace(/\{项目名称\}/g, name || '');
  }

  function copyText(text, btn, doneLabel) {
    var original = btn ? btn.textContent : '';
    function done() { if (btn) { btn.textContent = doneLabel || '已复制 ✓'; setTimeout(function () { btn.textContent = original; }, 2200); } }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () { fallback(); });
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { if (btn) btn.textContent = '请长按复制'; }
      document.body.removeChild(ta);
    }
  }

  function renderExchange() {
    var c = state.community;
    if (!c || !el('exchangeGrid')) return;
    var items = state.activeExchange === 'offers' ? (c.offers || []) : (c.requests || []);
    el('offerCount').textContent = (c.offers || []).length;
    el('requestCount').textContent = (c.requests || []).length;
    el('exchangeGrid').innerHTML = items.map(function (o) {
      var isOffer = state.activeExchange === 'offers';
      var tags = (o.tags || []).map(function (t) { return '<span class="tag">' + escapeHtml(t) + '</span>'; }).join('');
      var mainLabel = isOffer ? '我能给' : '我需要';
      var mainVal = isOffer ? o.give : o.need;
      var secondLabel = isOffer ? '我想换' : '紧急度';
      var secondVal = isOffer ? o.want : o.urgency;
      return '<article class="ex-card"><div class="ex-head"><span class="ex-type">' +
        escapeHtml(isOffer ? '能力' : '需求') + '</span><h3>' + escapeHtml(o.name || '') + '</h3></div>' +
        '<div class="ex-field"><b>' + mainLabel + '</b><span>' + escapeHtml(mainVal || '') + '</span></div>' +
        '<div class="ex-field"><b>' + secondLabel + '</b><span>' + escapeHtml(secondVal || '') + '</span></div>' +
        '<div class="ex-field"><b>为什么</b><span>' + escapeHtml(o.why || '') + '</span></div>' +
        '<div class="tags">' + tags + '</div>' +
        '<div class="ex-foot"><span class="ex-status">' + escapeHtml(o.status || '') + '</span>' +
        '<button class="claim-btn" data-name="' + escapeHtml(o.name || '') + '">认领 / 发起 →</button></div></article>';
    }).join('');
    Array.prototype.forEach.call(el('exchangeGrid').querySelectorAll('.claim-btn'), function (btn) {
      btn.addEventListener('click', function () {
        var msg = applyTemplate(c.meta.contact.template, btn.getAttribute('data-name'));
        copyText(msg, btn, '文案已复制 ✓');
      });
    });
    el('exchangeStatus').textContent = c.meta.statusNote || '';
    el('exchangeRedline').textContent = '红线：' + (c.meta.redlines || []).join(' · ');
  }

  function renderColumns() {
    var c = state.community;
    if (!c || !el('columnGrid')) return;
    state.columns = c.columns || [];
    el('columnGrid').innerHTML = (c.columns || []).map(function (v, idx) {
      return '<article class="col-card"><div class="col-meta"><span>' + escapeHtml(v.kicker || '') +
        '</span><span>' + escapeHtml(v.date || '') + ' · ' + escapeHtml(v.read || '') + '</span></div>' +
        '<h3>' + escapeHtml(v.title || '') + '</h3>' +
        '<p class="col-stand">' + escapeHtml(v.stand || '') + '</p>' +
        '<button class="read-btn" data-idx="' + idx + '">展开全文 ↓</button>' +
        '<div class="col-body" id="colbody-' + idx + '">' +
        (v.sections || []).map(function (s) { return '<h4>' + escapeHtml(s.h || '') + '</h4><p>' + escapeHtml(s.p || '') + '</p>'; }).join('') +
        '<p class="col-cta">' + escapeHtml(v.cta || '') + '</p></div></article>';
    }).join('');
    Array.prototype.forEach.call(el('columnGrid').querySelectorAll('.read-btn'), function (btn) {
      btn.addEventListener('click', function () {
        var body = el('colbody-' + btn.getAttribute('data-idx'));
        var open = body.classList.toggle('open');
        btn.textContent = open ? '收起 ↑' : '展开全文 ↓';
      });
    });
  }

  function renderEvents() {
    var c = state.community;
    if (!c || !el('eventGrid')) return;
    el('eventGrid').innerHTML = (c.events || []).map(function (e) {
      var tags = (e.fee ? [e.fee] : []).concat([e.type || '']).map(function (t) {
        return '<span class="tag">' + escapeHtml(t) + '</span>';
      }).join('');
      return '<article class="ev-card"><div class="ev-head"><span class="ev-online">' +
        escapeHtml((e.type || '').indexOf('线上') >= 0 ? '线上' : '线下') + '</span>' +
        '<h3>' + escapeHtml(e.name || '') + '</h3></div>' +
        '<div class="ev-when">' + escapeHtml(e.when || '') + '</div>' +
        '<div class="ev-where">' + escapeHtml(e.where || '') + ' · 发起：' + escapeHtml(e.host || '') + '</div>' +
        '<p>' + escapeHtml(e.note || '') + '</p>' +
        '<div class="tags">' + tags + '</div>' +
        '<div class="ev-foot"><span class="ex-status">' + escapeHtml(e.status || '') + '</span>' +
        '<button class="claim-btn" data-name="' + escapeHtml((e.name || '') + '（' + (e.when || '') + '）') + '">我要参加 / 发起 →</button></div></article>';
    }).join('');
    Array.prototype.forEach.call(el('eventGrid').querySelectorAll('.claim-btn'), function (btn) {
      btn.addEventListener('click', function () {
        var msg = applyTemplate(c.meta.contact.template, btn.getAttribute('data-name'));
        copyText(msg, btn, '报名文案已复制 ✓');
      });
    });
  }

  function renderCommunity() {
    renderExchange();
    renderColumns();
    renderEvents();
    var c = state.community;
    if (c && el('exchangeCta')) {
      el('exchangeCta').addEventListener('click', function () {
        copyText(c.meta.contact.template, this, '发起文案已复制 ✓');
      });
    }
    var tabs = el('exchangeTabs');
    if (tabs) {
      Array.prototype.forEach.call(tabs.querySelectorAll('.etab'), function (btn) {
        btn.addEventListener('click', function () {
          state.activeExchange = btn.getAttribute('data-tab');
          Array.prototype.forEach.call(tabs.querySelectorAll('.etab'), function (b) { b.classList.remove('active'); });
          btn.classList.add('active');
          renderExchange();
        });
      });
    }
  }

  // ============ 开台人：立场 + 递话筒 ============
  function hostReply(topic) {
    var h = state.host;
    var tpl = h && h.meta && h.meta.replyTemplate;
    return applyTemplate(tpl, topic);
  }

  function renderHost() {
    var h = state.host;
    if (!h || !el('hostOpening')) return;
    var meta = h.meta || {};

    if (el('hostRoleNote')) el('hostRoleNote').textContent = meta.roleNote || '';
    if (el('hostPrinciple')) el('hostPrinciple').textContent = '立台原则：' + (meta.principle || '');

    // 开台白
    var o = h.opening || {};
    var oSections = (o.sections || []).map(function (s) {
      return '<div class="host-sec"><h4>' + escapeHtml(s.h || '') + '</h4><p>' + escapeHtml(s.p || '') + '</p></div>';
    }).join('');
    el('hostOpening').innerHTML =
      '<div class="host-card"><div class="host-kicker">' + escapeHtml(o.kicker || '') + '</div>' +
      '<h3>' + escapeHtml(o.title || '') + '</h3>' +
      '<p class="host-stand">' + escapeHtml(o.stand || '') + '</p>' +
      '<div class="host-body">' + oSections + '</div>' +
      '<div class="handoff"><span class="handoff-label">递话筒 ↓</span>' +
      '<p>' + escapeHtml(o.handoff || '') + '</p>' +
      '<button class="claim-btn host-reply" data-topic="' + escapeHtml(o.title || '开台白') + '">接这个话 →</button></div></div>';

    // 本周擂台
    el('roundGrid').innerHTML = (h.rounds || []).map(function (r) {
      return '<article class="round-card">' +
        '<div class="round-meta"><span>' + escapeHtml(r.kicker || '') + '</span><span>' + escapeHtml(r.week || '') + '</span></div>' +
        '<h3>' + escapeHtml(r.question || '') + '</h3>' +
        '<div class="round-block take"><b>我的倾向</b><p>' + escapeHtml(r.myTake || '') + '</p></div>' +
        '<div class="round-block other"><b>反方这么说</b><p>' + escapeHtml(r.otherSide || '') + '</p></div>' +
        '<div class="round-block why"><b>为什么问这个</b><p>' + escapeHtml(r.whyAsk || '') + '</p></div>' +
        '<div class="handoff"><span class="handoff-label">递话筒 ↓</span>' +
        '<p>' + escapeHtml(r.handoff || '') + '</p>' +
        '<button class="claim-btn host-reply" data-topic="' + escapeHtml(r.question || '') + '">接这个话 →</button></div>' +
        '<div class="round-status">' + escapeHtml(r.status || '') + '</div></article>';
    }).join('');

    // 回声墙
    el('echoGrid').innerHTML =
      '<p class="echo-note">' + escapeHtml(meta.echoNote || '') + '</p>' +
      (h.echoes || []).map(function (e) {
        return '<article class="echo-card"><p class="echo-voice">“' + escapeHtml(e.voice || '') + '”</p>' +
          '<div class="echo-foot"><span>' + escapeHtml(e.from || '') + '</span>' +
          '<span>回应「' + escapeHtml(e.to || '') + '」 · ' + escapeHtml(e.status || '') + '</span></div></article>';
      }).join('');

    // 站规
    el('rulesGrid').innerHTML = (h.rules || []).map(function (r) {
      return '<div class="rule-card"><span class="rule-n">' + escapeHtml(r.n || '') + '</span>' +
        '<div><h4>' + escapeHtml(r.title || '') + '</h4><p>' + escapeHtml(r.body || '') + '</p>' +
        '<span class="rule-from">' + escapeHtml(r.from || '') + '</span></div></div>';
    }).join('');

    Array.prototype.forEach.call(document.querySelectorAll('.host-reply'), function (btn) {
      btn.addEventListener('click', function () {
        copyText(hostReply(btn.getAttribute('data-topic')), btn, '接话文案已复制 ✓');
      });
    });
  }

  function initNav() {
    var toggle = el('navToggle');
    var nav = el('nav');
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  function showError(message) {
    var main = document.querySelector('main');
    var box = document.createElement('div');
    box.className = 'wrap';
    box.innerHTML = '<div class="error">数据加载失败：' + escapeHtml(message) +
      '<br>本地预览请通过 HTTP 服务访问（例如 <code>python -m http.server 8000</code>），不要直接双击打开 HTML 文件。</div>';
    main.insertBefore(box, main.firstChild);
  }

  function boot() {
    initNav();
    Promise.all([
      fetch('content.json', { cache: 'no-store' }).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      }),
      fetch('businesses.json', { cache: 'no-store' }).then(function (r) {
        return r.ok ? r.json() : null;
      }).catch(function () { return null; }),
      fetch('community.json', { cache: 'no-store' }).then(function (r) {
        return r.ok ? r.json() : null;
      }).catch(function () { return null; }),
      fetch('host.json', { cache: 'no-store' }).then(function (r) {
        return r.ok ? r.json() : null;
      }).catch(function () { return null; })
    ])
      .then(function (res) {
        var data = res[0];
        var biz = res[1];
        state.community = res[2];
        state.host = res[3];
        if (biz && biz.businesses && biz.businesses.length) {
          state.bizMeta = biz;
          data.businesses = biz.businesses;
        }
        state.data = data;
        renderSite(data);
      })
      .catch(function (err) { showError(err.message || String(err)); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
