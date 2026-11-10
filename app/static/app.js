(function () {
  'use strict';

  var form = document.getElementById('add-form');
  var input = document.getElementById('new-task');
  var errorEl = document.getElementById('error-message');
  var emptyEl = document.getElementById('empty-message');
  var listEl = document.getElementById('task-list');
  var GENERIC_ERROR = 'Something went wrong. Please try again.';

  function showError(msg) {
    errorEl.textContent = msg || GENERIC_ERROR;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.textContent = '';
    errorEl.hidden = true;
  }

  // Returns parsed JSON body; throws Error with .status and .serverMessage on failure.
  function api(method, url, body) {
    var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) {
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        if (text) {
          try { data = JSON.parse(text); } catch (e) { data = null; }
        }
        if (!res.ok) {
          var err = new Error('request failed');
          err.status = res.status;
          err.serverMessage = data && typeof data.error === 'string' ? data.error : null;
          throw err;
        }
        return data;
      });
    });
  }

  function handleError(err) {
    if (err && err.status === 404) {
      showError(err.serverMessage || 'Task not found.');
      loadTasks(true);
    } else if (err && err.status >= 400 && err.status < 500 && err.serverMessage) {
      showError(err.serverMessage);
    } else {
      showError(GENERIC_ERROR);
    }
  }

  function makeButton(text, cls, label, onClick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = text;
    if (cls) { b.className = cls; }
    b.setAttribute('aria-label', label);
    b.addEventListener('click', onClick);
    return b;
  }

  function renderTask(task) {
    var li = document.createElement('li');
    li.className = 'task' + (task.completed ? ' completed' : '');
    li.setAttribute('data-id', String(task.id));

    var desc = document.createElement('span');
    desc.className = 'description';
    desc.textContent = task.description;
    li.appendChild(desc);

    var actions = document.createElement('div');
    actions.className = 'actions';
    actions.appendChild(makeButton(
      task.completed ? 'Mark pending' : 'Complete', 'secondary',
      (task.completed ? 'Mark as pending: ' : 'Mark as complete: ') + task.description,
      function () { toggleTask(task); }));
    actions.appendChild(makeButton('Edit', 'secondary', 'Edit task: ' + task.description,
      function () { startEdit(li, task); }));
    actions.appendChild(makeButton('Delete', 'danger', 'Delete task: ' + task.description,
      function () { deleteTask(task); }));
    li.appendChild(actions);
    return li;
  }

  function render(tasks) {
    while (listEl.firstChild) { listEl.removeChild(listEl.firstChild); }
    tasks.forEach(function (t) { listEl.appendChild(renderTask(t)); });
    emptyEl.hidden = tasks.length > 0;
  }

  function loadTasks(keepError) {
    return api('GET', '/api/tasks').then(function (data) {
      if (!keepError) { clearError(); }
      render(Array.isArray(data) ? data : []);
    }).catch(function () {
      showError(GENERIC_ERROR);
    });
  }

  function toggleTask(task) {
    clearError();
    api('PATCH', '/api/tasks/' + encodeURIComponent(task.id), { completed: !task.completed })
      .then(function () { return loadTasks(); })
      .catch(handleError);
  }

  function deleteTask(task) {
    clearError();
    api('DELETE', '/api/tasks/' + encodeURIComponent(task.id))
      .then(function () { return loadTasks(); })
      .catch(handleError);
  }

  function startEdit(li, task) {
    clearError();
    while (li.firstChild) { li.removeChild(li.firstChild); }

    var editForm = document.createElement('form');
    editForm.className = 'edit-form';

    var field = document.createElement('input');
    field.type = 'text';
    field.value = task.description;
    field.maxLength = 255;
    field.required = true;
    field.setAttribute('aria-label', 'Edit description for task: ' + task.description);
    editForm.appendChild(field);

    var actions = document.createElement('div');
    actions.className = 'actions';
    var save = document.createElement('button');
    save.type = 'submit';
    save.textContent = 'Save';
    save.setAttribute('aria-label', 'Save changes to task: ' + task.description);
    var cancel = makeButton('Cancel', 'secondary', 'Cancel editing task: ' + task.description,
      function () { loadTasks(); });
    actions.appendChild(save);
    actions.appendChild(cancel);
    editForm.appendChild(actions);

    editForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var value = field.value.trim();
      if (!value) { showError('Description must not be empty.'); return; }
      clearError();
      api('PATCH', '/api/tasks/' + encodeURIComponent(task.id), { description: value })
        .then(function () { return loadTasks(); })
        .catch(function (err) {
          // keep the edit form open so the user's text is not lost
          handleError(err);
        });
    });
    editForm.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { ev.preventDefault(); loadTasks(); }
    });

    li.appendChild(editForm);
    field.focus();
    field.select();
  }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var value = input.value.trim();
    if (!value) { showError('Description must not be empty.'); return; }
    clearError();
    api('POST', '/api/tasks', { description: value })
      .then(function () {
        input.value = '';
        return loadTasks();
      })
      .catch(handleError);
  });

  loadTasks();
})();
