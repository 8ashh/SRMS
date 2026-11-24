def test_login_logout_flow(client, init_sample_data):
    # 1. Valid login as admin
    resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data or b"Admin Dashboard" in resp.data

    # 2. Logout
    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"logged out" in logout_resp.data

def test_invalid_login(client, init_sample_data):
    resp = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data

def test_role_based_access_protection(client, init_sample_data):
    # Unauthenticated user visiting admin dashboard is redirected to login
    resp = client.get('/admin/dashboard', follow_redirects=False)
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

    # Student logging in should NOT be able to access /admin/dashboard
    client.post('/login', data={'username': 'st001', 'password': 'st001@123'}, follow_redirects=True)
    admin_attempt = client.get('/admin/dashboard', follow_redirects=True)
    assert b"Access denied" in admin_attempt.data or b"Student Portal" in admin_attempt.data

def test_student_data_isolation(client, init_sample_data):
    # Log in as Student 1 (st001)
    client.post('/login', data={'username': 'st001', 'password': 'st001@123'}, follow_redirects=True)

    # Attempt to download Student 2's PDF dossier
    resp = client.get('/reports/student/2/pdf', follow_redirects=True)
    assert resp.status_code == 200
    assert b"Unauthorized" in resp.data
