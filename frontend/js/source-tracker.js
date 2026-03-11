window.SourceTracker = {
  update(sources = []) {
    const list = document.getElementById('sourceList');
    list.innerHTML = '';
    sources.forEach((src, i) => {
      const li = document.createElement('li');
      li.innerHTML = `${src.source} (${src.count || 0})`;
      if (i === 0) li.classList.add('source-active');
      list.appendChild(li);
    });
  }
};
