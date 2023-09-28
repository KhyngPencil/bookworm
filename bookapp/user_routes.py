import json,requests,random,string
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template,request,abort,redirect,flash,make_response,session,url_for

#local Imports

from bookapp import app,csrf,mail,Message
from bookapp.models import db,Book,User,Category,State,Lga,Reviews,Contact,Donation
from bookapp.forms import *

def login_required(f): #from functools import wraps
    @wraps(f)#thus ensures that details(meta data )about the original function f, that is being decorated is stll available...
    def login_check(*args,**kwargs):
        if session.get("userloggedin")!=None:
            return f(*args,**kwargs)
        else:
            flash("Access Denied")
            return redirect('/login')
    return login_check
#to use login_required, place it after the route decorator over any route that needs authentication



@app.route("/contact/")
def ajax_contact():
    data="I am s string coming from the server"
    return render_template('user/ajax_test.html',data=data)
 
@app.route("/submission/",methods=["GET","POST"])
def ajax_submission():
    '''This Route Will Be Visited By Ajax Silently'''
    user= request.form.get('fullname')
    if user != "" and user != None:
        return f"Thank you {user} for completing the form" 
    else:
        return "Please Complete The Form"

@app.route('/checkusername/',methods=["GET","POST"])
def checkusername():
    email=request.form.get('useemail')
    user=db.session.query(User).filter(User.user_email==email).first()
    if user:
        return "Email Taken"
    else:
        return "Email Is Okay, Go Ahead"

@app.route('/dependent/')
def dependent_dropdown():
    #write a query that will fetch all the sates from state atble
    states= db.session.query(State).all()
    return render_template('user/showstate.html',states=states)

@app.route('/lga/<stateid>/')
def load_lgas(stateid):
    records= db.session.query(Lga).filter(Lga.state_id==stateid).all()
    str2return= "<select class='form-control'>"
    for r in records:
        optstr= f"<option value='{r.lga_id}'>"+ r.lga_name+"</option>"
        str2return=str2return+optstr
    str2return= str2return+"</select>"  

    return str2return  




@app.route("/favorite/")
def favorite_topics():
    bootcamp={'name':'olusegun','Topics':['html','css','python']}
    
    cats=db.session.query(Category).all()
    # for c in cats:
    #     category=[]
    #     category.append(c.cat_name)
    category=[c.cat_name for c in cats]
    return json.dumps(category)

@app.after_request
def after_request(response):
    #TO solve teh problem of loggedout user's details being cached in the browser 
    response.headers['Cache-Control']="no-cache, no-store, must-revalidate"
    return response

@app.route('/changedp/',methods=["GET","POST"])
@login_required
def changedp():
    id =session.get('userloggedin')
    userdeets=db.session.query(User).get(id)
    dpform=DpForm()
    if request.method=='GET':        
        return render_template('user/changedp.html',dpform=dpform,userdeets=userdeets)
    else:
        if dpform.validate_on_submit():
            pix= request.files.get('dp')
            filename=pix.filename
            pix.save(app.config['USER_PROFILE_PATH']+filename)
            userdeets.user_pix=filename
            db.session.commit()
            flash ("FIle Will Be Uploaded")
            return redirect(url_for('dashboard'))
        else:
            return render_template('user/changedp.html',dpform=dpform,userdeets=userdeets)

@app.route('/profile/',methods=['GET','POST'])
@login_required
def edit_profile():
    id=session.get('userloggedin')
    userdeets=db.session.query(User).get(id)
    pform=ProfileForm()
    if request.method =='GET':
        return render_template('user/edit_profile.html',pform=pform,userdeets=userdeets)
    else:
        if pform.validate_on_submit():
            fname=request.form.get('fullname')            
            userdeets.user_fullname=fname
            db.session.commit()
            flash("Thank You, Profile Updated")
            return redirect(url_for('dashboard'))
        else:
            return "Failed"

@app.route('/submit_review/',methods=['POST'])
def submit_review():
    title=request.form.get('title')
    content=request.form.get('content')
    userid= session.get('userloggedin')
    bookid= request.form.get('bookid')
    write=Reviews(rev_title=title,rev_text=content,rev_userid=userid,rev_bookid=bookid)
    db.session.add(write)
    db.session.commit()
    retstr = f'''<article class="blog-post">
      <h5 class="blog-post-title">{title}</h5>
      <p class="blog-post-meta">Reviwed just now by <a href="#">{write.reviewby.user_fullname}</a></p>

      <p>{content}</p>
      <hr> 
    </article>''' 
    return retstr  


# home page
@app.route("/")
def home_page():
    books = db.session.query(Book).filter(Book.book_status == '1').limit(4).all()
    # connect to the endpoint http:127.0.0.1:1995/api/v1.0/listall to collect data of book
    # pas it to th templates and display on the template
    try:
        response = requests.get('http://127.0.0.1:5000/api/v1.0/listall/')
        # import requests
        rsp = json.loads(response.text)#response.json
    except:
        rsp = None #if the server is unreacheable...
    return render_template("user/home_page.html",books=books,rsp=rsp)

    


@app.route('/book/deatails/<id>')
def book_details(id):
    book= db.session.query(Book).get_or_404(id)
    return render_template('user/reviews.html', book=book)

def generate_string(howmany):
    x= random.sample(string.digits,howmany)
    return ''.join(x)

url="https://api.paystack.co/transaction/initialize"


@app.route('/landing')
@login_required
def landing():
    refno = session.get('trxno')
    transaction_deets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    #make a curl request to paystack end point 
    url="https://api.paystack.co/transaction/verify/"+transaction_deets.don_refno
    headers ={"Content_Type=":"application/json", "Authorization": "Bearer sk_test_28870d0734969f136ee42f051102b2f03a9ff845"}
    response =  requests.get(url,headers=headers)
    rspjson = json.loads(response.text)
    if rspjson['status']== True:
        paystatus =rspjson['data']['gateway_response']
        transaction_deets.don_status ='Paid'
        db.session.commit()
        return redirect("/dashboard")
    else:
        flash("payment failed")
        return redirect('/reports')#dsiplay all the payment reports
    
@app.route('/reports')
@login_required
def route():
    return "Error"

@app.route("/initialize/paystack")
@login_required
def initialize_paystack():
    deets = User.query.get(session['userloggedin'])
    #transaction details
    refno =session.get('trxno')
    transaction_deets=db.session.query(Donation).filter(Donation.don_refno==refno).first()
    #make a call to the paystack endpoint
    url="https://api.paystack.co/transaction/initialize"
    headers={"content_type":"Content-Type: application/json","Authorization":"Bearer sk_test_28870d0734969f136ee42f051102b2f03a9ff845"
    }
    data={"email":deets.user_email ,"amount":transaction_deets.don_amt,"reference":refno }
    response= requests.post(url,headers=headers,data=json.dumps(data))
    #extrect json from the response coming from paystack
    rspjson= response.json()
    # return rspjson
    if rspjson['status']==True:
        redirectURL=rspjson['data']['authorization_url']
        return redirect(redirectURL)#paystack payment page will load
    else:
        flash ("Please Complete The Form Again")
        return redirect('/donate')


    


@app.route('/donate',methods=["GET","POST"])
@login_required
def donation():
    if request.method=="GET":
        deets=db.session.query(User).get(session['userloggedin'])
        return render_template('user/donation.html',deets=deets)
    else:
       
        #retrieve form data
        amt=float(request.form.get('amount'))*100
        donor=request.form.get('fullname')
        email=request.form.get('email')

            #generate a transaction reference
        ref= 'BW'+str(generate_string(8))
        #insert into db
        donation=Donation(don_amt=amt,don_userid=session['userloggedin'],don_email=email,don_fullname=donor,don_status='pending',don_refno=ref)
        db.session.add(donation)
        db.session.commit()
        #save the reference no in session
        session['trxno']=ref
        #redirect to a confirmation page
        return redirect("/confirm_donation")
        
        
       
        
        
@app.route('/confirm_donation')
@login_required
def confirm_donation():
    "We want to display the details of the transaction saved from the previous page"
    deets=db.session.query(User).get(session['userloggedin'])
    if session.get('trxno')==None: #means they are visiting here directly
        flash("Please Complete This Form",category='error')
    else:
        donation_deets=Donation.query.filter(Donation.don_refno==session['trxno']).first()
        return render_template("user/donation_confirmation.html",dd=donation_deets)

    

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='GET':
        return render_template('user/loginpage.html')
    else:
        email= request.form.get('email')
        pwd=request.form.get('pwd')
        deets= db.session.query(User).filter(User.user_email==email).first()
        if deets != None:
            hashed_pwd=deets.user_pwd
            if check_password_hash(hashed_pwd,pwd)== True:
                session['userloggedin']=deets.user_id
                return redirect('/dashboard')
            else:
                flash ('Invalid Credentials, Try Again')
                return redirect("/login")
        else:
            flash ('Invalid Credentials, Try Again')
            return redirect("/login")
@app.route("/myreviews/")
@login_required
def myreviews():
    id=session['userloggedin']
    userdeets=db.session.query(User).get(id)
    return render_template('user/myreviews.html',userdeets=userdeets)

@app.route('/sendmail')
def send_mail():
    file=open('requirements.txt')
    msg=Message(subject="Adding Heading Email From Bookworm ",sender='From Bookworm',recipients=['kaneb2841@gmail.com'])
    msg.html="""<h1>Welcome Home</h1>
                <img src='https://images.pexels.com/photos/325044/pexels-photo-325044.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1'><hr>"""
    msg.attach('saved_as.txt','application/text',file.read())
    mail.send(msg)
    return "Done"
    

@app.route('/ajaxopt/',methods=['GET','POST'])
def ajax_options():
    cform=ContactForm()
    if request.method=='GET':
        return render_template('user/ajax_option.html',cform=cform)
    else:
        email= request.form.get('email')
        return f"Thank You, Your Email Has Been Added {email}"

@app.route('/logout/')
def logout():
    if session.get("userloggedin") != None:
        session.pop("userloggedin",None)
    return redirect('/') 

@app.route('/viewall/')
def viewall():
    books=db.session.query(Book).filter(Book.book_status=='1').all()
    return render_template('user/viewall.html',books=books) 


@app.route('/dashboard')
def dashboard():
    if session.get("userloggedin") != None:
        id= session.get("userloggedin")
        userdeets= User.query.get(id)
        return render_template('user/dashboard.html',userdeets=userdeets)
    else:
        flash("You Need To login to access this page")
        return redirect('/login')

@app.route('/register/',methods=["GET","POST"])
def register():
    regform=RegForm()
    if request.method =="GET":
       
        return render_template('user/signup.html',regform=regform)
    else:
        if regform.validate_on_submit():
            fname=request.form.get('fullname')
            email=request.form.get('email')
            pwd=request.form.get('pwd')
            hashed_pwd= generate_password_hash(pwd)
            user=User(user_fullname=fname,user_email=email,user_pwd=hashed_pwd)
            db.session.add(user)
            db.session.commit()
            flash("An Account Has Been Created For You. Please Login")
            return redirect('/login')            
        else:
            return render_template('user/signup.html',regform=regform)
