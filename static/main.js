async function createRequest() {
  const name = document.getElementById('name').value || 'Anonymous';
  const priority = document.getElementById('priority').value;
  const resourceType = document.getElementById('resource_type').value;
  const est = document.getElementById('est_minutes').value || 60;

  const res = await fetch('/api/request', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
        name: name, 
        priority: priority, 
        resource_type: resourceType,
        est_minutes: est
    })
  });

  if (res.ok) {
    document.getElementById('name').value = '';
    refreshAll();
  } else {
    alert('Failed to create request');
  }
}

async function refreshAll() {
  await Promise.all([loadResources(), loadAllocations(), loadQueue()]);
}

async function loadResources() {
  const res = await fetch('/api/resources');
  const list = await res.json();
  let html = '<table><tr><th>ID</th><th>Label</th><th>Type</th><th>Status</th></tr>';
  for (const r of list) {
    const statusClass = r.status === 'free' ? 'status-free' : 'status-busy';
    html += `<tr class="${statusClass}"><td>${r.id}</td><td>${r.label}</td><td>${r.resource_type}</td><td>${r.status}</td></tr>`;
  }
  html += '</table>';
  document.getElementById('resources').innerHTML = html;
}

async function loadAllocations() {
  const res = await fetch('/api/allocations');
  const list = await res.json();
  let html = '<table><tr><th>ID</th><th>Patient</th><th>Needed</th><th>Assigned Resource</th><th>Allocated At</th><th>Action</th></tr>';
  for (const a of list) {
    html += `<tr>
      <td>${a.id}</td>
      <td>${a.name} (P${a.priority})</td>
      <td>${a.required_resource}</td>
      <td>${a.resource_type} #${a.resource_id}</td>
      <td>${new Date(a.allocated_at).toLocaleTimeString()}</td>
      <td><button onclick="release(${a.id})">Release</button></td>
    </tr>`;
  }
  html += '</table>';
  document.getElementById('allocations').innerHTML = html;
}

async function loadQueue() {
  const res = await fetch('/api/requests');
  const list = await res.json();
  const queued = list.filter(r => r.status === 'queued');
  
  let html = '<table><tr><th>ID</th><th>Name</th><th>Needed</th><th>Base Priority</th><th>Wait Time (s)</th><th>Effective Priority</th></tr>';
  
  // Calculate client-side estimation of effective priority for display
  const now = new Date();
  
  for (const r of queued) {
    const reqTime = new Date(r.requested_at + "Z"); // Treat as UTC
    const waitSeconds = Math.floor((now - reqTime) / 1000);
    const agingInterval = 30; // Must match server AGING_INTERVAL
    const boost = Math.floor(waitSeconds / agingInterval);
    const eff = Math.max(1, r.priority - boost);

    html += `<tr>
      <td>${r.id}</td>
      <td>${r.name}</td>
      <td><b>${r.required_resource}</b></td>
      <td>${r.priority}</td>
      <td>${waitSeconds}s</td>
      <td><strong>${eff}</strong></td>
    </tr>`;
  }
  html += '</table>';
  
  if (queued.length === 0) html = '<em>No queued requests</em>';
  document.getElementById('queue').innerHTML = html;
}

async function release(allocation_id) {
  const res = await fetch('/api/release', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({allocation_id})
  });
  if (res.ok) refreshAll();
}

// Auto-refresh every 2 seconds to see the scheduler work in real time
setInterval(refreshAll, 2000);
refreshAll();