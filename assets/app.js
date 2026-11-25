(function () {
  'use strict';

  var state = { data: null, activeCategory: '全部' };

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
      }).catch(function () { return null; })
    ])
      .then(function (res) {
        var data = res[0];
        var biz = res[1];
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
