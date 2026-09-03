from flask import Flask,request,redirect,url_for,session,render_template_string,flash,Response
import sqlite3,json,os,csv,io
from functools import wraps
from datetime import date
from werkzeug.security import generate_password_hash,check_password_hash
BASE=os.path.dirname(__file__);DB=os.path.join(BASE,"pickup.db");SEED=os.path.join(BASE,"seed.json")
app=Flask(__name__);app.secret_key=os.environ.get("SECRET_KEY","change-this-secret-key")
SCHEMA="CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'staff');CREATE TABLE IF NOT EXISTS pickups(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT NOT NULL,location TEXT NOT NULL,pickup_type TEXT NOT NULL,lot_no TEXT,parcels TEXT,pickup_by TEXT,booked_by TEXT,vehicle_type TEXT,pickup_status TEXT,software_update TEXT,remarks TEXT,created_by INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP);"
def db(): c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def opts(): return json.load(open(SEED,encoding="utf-8"))
def init_db():
 c=db();c.executescript(SCHEMA)
 if c.execute("SELECT COUNT(*) FROM users").fetchone()[0]==0:c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",("admin",generate_password_hash("admin123"),"admin"))
 if c.execute("SELECT COUNT(*) FROM pickups").fetchone()[0]==0:
  for r in opts()["records"]: c.execute("INSERT INTO pickups(date,location,pickup_type,lot_no,parcels,pickup_by,booked_by,vehicle_type,pickup_status,software_update,remarks) VALUES(?,?,?,?,?,?,?,?,?,?,?)",tuple(r[k] for k in ["date","location","pickup_type","lot_no","parcels","pickup_by","booked_by","vehicle_type","pickup_status","software_update","remarks"]))
 c.commit();c.close()
def login_required(f):
 @wraps(f)
 def w(*a,**kw):
  return f(*a,**kw) if "uid" in session else redirect(url_for("login"))
 return w
def admin_required(f):
 @wraps(f)
 def w(*a,**kw): return f(*a,**kw) if session.get("role")=="admin" else ("Admin access required",403)
 return w
BASE_HTML="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{{title}} - Pickup Management</title><style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#172033}.nav{background:#101828;color:#fff;padding:14px 22px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}.brand{font-weight:800;margin-right:auto}.nav a{color:#d0d5dd;text-decoration:none;font-size:14px}.wrap{max-width:1450px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:18px}.top h1{margin:0;font-size:25px}.muted{color:#667085;font-size:13px}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}.card,.panel{background:#fff;border:1px solid #e4e7ec;border-radius:12px;padding:17px}.num{font-size:28px;font-weight:800;margin-top:5px}.panel{margin-top:18px}.form{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.field label{display:block;font-size:12px;font-weight:700;margin-bottom:6px}.field input,.field select,.field textarea{width:100%;padding:10px;border:1px solid #d0d5dd;border-radius:8px;font:inherit}.field textarea{min-height:72px}.wide{grid-column:span 2}.btn{border:0;border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}.primary{background:#175cd3;color:#fff}.secondary{background:#eef2f6;color:#344054}.danger{background:#fee4e2;color:#b42318}.filters{display:grid;grid-template-columns:2fr repeat(4,1fr);gap:10px}.tablewrap{overflow:auto;margin-top:14px}.table{width:100%;border-collapse:collapse;min-width:1250px}.table th,.table td{padding:9px;border-bottom:1px solid #eaecf0;text-align:left;font-size:12px}.table th{background:#f9fafb;font-size:11px}.badge{padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800}.done,.yes{background:#dcfae6;color:#067647}.pending{background:#fef0c7;color:#b54708}.cancelled,.no{background:#fee4e2;color:#b42318}.flash{padding:10px 12px;background:#ecfdf3;color:#067647;border-radius:8px;margin-bottom:12px}.error{background:#fef3f2;color:#b42318}.login{max-width:420px;margin:12vh auto}.locs{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.loc{border:1px solid #e4e7ec;border-radius:9px;padding:12px}.loc strong{display:block;font-size:20px;margin-top:4px}@media(max-width:1050px){.cards{grid-template-columns:repeat(3,1fr)}.form{grid-template-columns:repeat(2,1fr)}.locs{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.wrap{padding:14px}.cards{grid-template-columns:repeat(2,1fr)}.form,.filters{grid-template-columns:1fr}.wide{grid-column:span 1}}
</style></head><body><div class=nav><div class=brand>Pickup Management</div>{% if session.get('uid') %}<a href='{{url_for("dashboard")}}'>Dashboard</a><a href='{{url_for("new_pickup")}}'>New Pickup</a><a href='{{url_for("pickups")}}'>Pickup List</a>{% if session.get('role')=='admin' %}<a href='{{url_for("users")}}'>Users</a>{% endif %}<a href='{{url_for("logout")}}'>Logout ({{session.get("username")}})</a>{% endif %}</div><div class=wrap>{% with msgs=get_flashed_messages(with_categories=true) %}{% for cat,msg in msgs %}<div class='flash {{ "error" if cat=="error" else "" }}'>{{msg}}</div>{% endfor %}{% endwith %}{{body|safe}}</div></body></html>"""
def page(title,body,**ctx): return render_template_string(BASE_HTML,title=title,body=render_template_string(body,**ctx))
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  c=db();u=c.execute("SELECT * FROM users WHERE username=?",(request.form["username"],)).fetchone();c.close()
  if u and check_password_hash(u["password_hash"],request.form["password"]):session.update(uid=u["id"],username=u["username"],role=u["role"]);return redirect(url_for("dashboard"))
  flash("Invalid username or password","error")
 return page("Login","""<div class='login panel'><h1>Pickup Management</h1><p class=muted>Sign in to continue</p><form method=post><div class=field><label>Username</label><input name=username required></div><br><div class=field><label>Password</label><input name=password type=password required></div><br><button class='btn primary'>Login</button></form><p class=muted>Initial admin: admin / admin123</p></div>""")
@app.route("/logout")
def logout():session.clear();return redirect(url_for("login"))
@app.route("/")
@login_required
def dashboard():
 c=db();a=[c.execute("SELECT COUNT(*) n FROM pickups").fetchone()["n"],c.execute("SELECT COUNT(*) n FROM pickups WHERE pickup_status='Done'").fetchone()["n"],c.execute("SELECT COUNT(*) n FROM pickups WHERE pickup_status='Pending' OR pickup_status=''").fetchone()["n"],c.execute("SELECT COUNT(*) n FROM pickups WHERE pickup_status='Cancelled'").fetchone()["n"],c.execute("SELECT COUNT(*) n FROM pickups WHERE software_update='Yes'").fetchone()["n"],c.execute("SELECT COUNT(*) n FROM pickups WHERE software_update='No'").fetchone()["n"]];locs=c.execute("SELECT location,COUNT(*) n FROM pickups GROUP BY location ORDER BY n DESC").fetchall();c.close()
 return page("Dashboard","""<div class=top><div><h1>Dashboard</h1><div class=muted>Pickup operations overview</div></div><a class='btn primary' href='{{url_for("new_pickup")}}'>+ New Pickup</a></div><div class=cards>{% for x in [('Total Pickups',a[0]),('Completed',a[1]),('Pending',a[2]),('Cancelled',a[3]),('Software Updated',a[4]),('Software Pending',a[5])] %}<div class=card><div class=muted>{{x[0]}}</div><div class=num>{{x[1]}}</div></div>{% endfor %}</div><div class=panel><h2>Location-wise Pickups</h2><div class=locs>{% for r in locs %}<div class=loc>{{r.location}}<strong>{{r.n}}</strong><span class=muted>pickups</span></div>{% endfor %}</div></div>""",a=a,locs=locs)
FORM="""<div class=top><div><h1>{{'Edit Pickup' if edit else 'New Pickup'}}</h1><div class=muted>Enter pickup details</div></div><a class='btn secondary' href='{{url_for("pickups")}}'>View List</a></div><div class=panel><form method=post class=form>
<div class=field><label>Date</label><input type=date name=date value='{{r.date if r else today}}' required></div><div class=field><label>Location</label><select name=location required><option value=''>Select...</option>{% for x in o.locations %}<option value='{{x}}' {{'selected' if r and r.location==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Pickup Type</label><select name=pickup_type required><option value=''>Select...</option>{% for x in o.pickup_types %}<option value='{{x}}' {{'selected' if r and r.pickup_type==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Lot No.</label><input name=lot_no value='{{r.lot_no if r}}'></div><div class=field><label>No. of Parcels</label><input name=parcels value='{{r.parcels if r}}'></div><div class=field><label>Pickup By</label><select name=pickup_by><option value=''>Select...</option>{% for x in o.people %}<option value='{{x}}' {{'selected' if r and r.pickup_by==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Booked By</label><select name=booked_by><option value=''>Select...</option>{% for x in o.people %}<option value='{{x}}' {{'selected' if r and r.booked_by==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Vehicle Type</label><select name=vehicle_type><option value=''>Select...</option>{% for x in o.vehicles %}<option value='{{x}}' {{'selected' if r and r.vehicle_type==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Pickup Status</label><select name=pickup_status><option value=''>Select...</option>{% for x in o.statuses %}<option value='{{x}}' {{'selected' if r and r.pickup_status==x}}>{{x}}</option>{% endfor %}</select></div><div class=field><label>Update in Software</label><select name=software_update><option value=''>Select...</option>{% for x in o.software %}<option value='{{x}}' {{'selected' if r and r.software_update==x}}>{{x}}</option>{% endfor %}</select></div><div class='field wide'><label>Remarks</label><textarea name=remarks>{{r.remarks if r}}</textarea></div><div class=wide><button class='btn primary'>Save Pickup</button></div></form></div>"""
@app.route("/pickup/new",methods=["GET","POST"])
@login_required
def new_pickup():
 if request.method=="POST":
  f=request.form;c=db();c.execute("INSERT INTO pickups(date,location,pickup_type,lot_no,parcels,pickup_by,booked_by,vehicle_type,pickup_status,software_update,remarks,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(f["date"],f["location"],f["pickup_type"],f.get("lot_no",""),f.get("parcels",""),f.get("pickup_by",""),f.get("booked_by",""),f.get("vehicle_type",""),f.get("pickup_status",""),f.get("software_update",""),f.get("remarks",""),session["uid"]));c.commit();c.close();flash("Pickup saved successfully");return redirect(url_for("pickups"))
 return page("New Pickup",FORM,o=opts(),r=None,edit=False,today=date.today().isoformat())
@app.route("/pickup/<int:pid>/edit",methods=["GET","POST"])
@login_required
def edit_pickup(pid):
 c=db();r=c.execute("SELECT * FROM pickups WHERE id=?",(pid,)).fetchone()
 if not r:c.close();return "Not found",404
 if request.method=="POST":
  f=request.form;c.execute("UPDATE pickups SET date=?,location=?,pickup_type=?,lot_no=?,parcels=?,pickup_by=?,booked_by=?,vehicle_type=?,pickup_status=?,software_update=?,remarks=? WHERE id=?",(f["date"],f["location"],f["pickup_type"],f["lot_no"],f["parcels"],f["pickup_by"],f["booked_by"],f["vehicle_type"],f["pickup_status"],f["software_update"],f["remarks"],pid));c.commit();c.close();flash("Pickup updated");return redirect(url_for("pickups"))
 c.close();return page("Edit Pickup",FORM,o=opts(),r=r,edit=True,today=date.today().isoformat())
def filtered():
 q=request.args.get("q","");loc=request.args.get("location","");status=request.args.get("status","");frm=request.args.get("from","");to=request.args.get("to","");sql="SELECT * FROM pickups WHERE 1=1";args=[]
 if q:sql+=" AND (location LIKE ? OR pickup_type LIKE ? OR pickup_by LIKE ? OR booked_by LIKE ? OR remarks LIKE ?)";args += [f"%{q}%"]*5
 if loc:sql+=" AND location=?";args.append(loc)
 if status:sql+=" AND pickup_status=?";args.append(status)
 if frm:sql+=" AND date>=?";args.append(frm)
 if to:sql+=" AND date<=?";args.append(to)
 sql+=" ORDER BY date DESC,id DESC";c=db();r=c.execute(sql,args).fetchall();c.close();return r
@app.route("/pickups")
@login_required
def pickups():
 return page("Pickup List","""<div class=top><div><h1>Pickup List</h1><div class=muted>{{rows|length}} records shown</div></div><div><a class='btn secondary' href='{{url_for("export_csv",**request.args)}}'>Export CSV</a> <a class='btn primary' href='{{url_for("new_pickup")}}'>+ New Pickup</a></div></div><div class=panel><form class=filters><input name=q placeholder='Search...' value='{{request.args.get("q","")}}'><input name=from type=date value='{{request.args.get("from","")}}'><input name=to type=date value='{{request.args.get("to","")}}'><select name=location><option value=''>All Locations</option>{% for x in o.locations %}<option value='{{x}}' {{'selected' if request.args.get("location")==x}}>{{x}}</option>{% endfor %}</select><select name=status><option value=''>All Statuses</option>{% for x in o.statuses %}<option value='{{x}}' {{'selected' if request.args.get("status")==x}}>{{x}}</option>{% endfor %}</select><button class='btn secondary'>Filter</button></form><div class=tablewrap><table class=table><tr><th>Sr</th><th>Date</th><th>Location</th><th>Pickup Type</th><th>Lot No.</th><th>Parcels</th><th>Pickup By</th><th>Booked By</th><th>Vehicle</th><th>Status</th><th>Software</th><th>Remarks</th><th>Action</th></tr>{% for r in rows %}<tr><td>{{loop.index}}</td><td>{{r.date}}</td><td>{{r.location}}</td><td>{{r.pickup_type}}</td><td>{{r.lot_no}}</td><td>{{r.parcels}}</td><td>{{r.pickup_by}}</td><td>{{r.booked_by}}</td><td>{{r.vehicle_type}}</td><td>{% if r.pickup_status %}<span class='badge {{ "done" if r.pickup_status=="Done" else "cancelled" if r.pickup_status=="Cancelled" else "pending" }}'>{{r.pickup_status}}</span>{% endif %}</td><td>{% if r.software_update %}<span class='badge {{ "yes" if r.software_update=="Yes" else "no" }}'>{{r.software_update}}</span>{% endif %}</td><td>{{r.remarks}}</td><td><a class='btn secondary' href='{{url_for("edit_pickup",pid=r.id)}}'>Edit</a></td></tr>{% endfor %}</table></div></div>""",rows=filtered(),o=opts())
@app.route("/export.csv")
@login_required
def export_csv():
 out=io.StringIO();w=csv.writer(out);w.writerow(["Sr No.","Date","Location","Pickup Type","Lot No.","No. of Parcels","Pickup By","Booked By","Vehicle Type","Pickup Status","Update in Software","Remarks"])
 for i,r in enumerate(filtered(),1):w.writerow([i]+[r[k] for k in ["date","location","pickup_type","lot_no","parcels","pickup_by","booked_by","vehicle_type","pickup_status","software_update","remarks"]])
 return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=pickup-register.csv"})
@app.route("/users")
@login_required
@admin_required
def users():
 c=db();rows=c.execute("SELECT username,role FROM users ORDER BY username").fetchall();c.close()
 return page("Users","""<div class=top><div><h1>User Management</h1><div class=muted>Add staff/admin accounts</div></div></div><div class=panel><form method=post action='{{url_for("add_user")}}' class=form><div class=field><label>Username</label><input name=username required></div><div class=field><label>Password</label><input name=password type=password required></div><div class=field><label>Role</label><select name=role><option>staff</option><option>admin</option></select></div><div><button class='btn primary'>Add User</button></div></form></div><div class=panel><table class=table><tr><th>Username</th><th>Role</th></tr>{% for r in rows %}<tr><td>{{r.username}}</td><td>{{r.role}}</td></tr>{% endfor %}</table></div>""",rows=rows)
@app.route("/users/add",methods=["POST"])
@login_required
@admin_required
def add_user():
 try:
  c=db();c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",(request.form["username"],generate_password_hash(request.form["password"]),request.form["role"]));c.commit();c.close();flash("User added")
 except Exception:flash("Could not add user","error")
 return redirect(url_for("users"))
if __name__=="__main__":init_db();app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
