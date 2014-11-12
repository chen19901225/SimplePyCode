
var sync_callback;
var sync_total;
var sync_finish;
if(typeof($SYS)==="undefined"){
    var $SYS={
        
    }
}
function get_cookie(b){
    if(typeof($SYS.cookie_pre)!=="undefined"){
        b=$SYS.cookie_pre+b;
    }
    var a=document.cookie.match(new RegExp("(^| )"+b+"=([^;]*)(;|$)"));
    if(a!==null){
        return decodeURIComponent(a[2]);
    }
    return null;
}
function setCookie(c,d,e){
    e=e||0;
    var a="";
    if(e!==0){
        var b=new Date();
        b.setTime(b.getTime()+(e*1000));
        a="; expires="+b.toGMTString();
    }
    if(typeof($SYS.cookie_pre)!=="undefined"){
        c=$SYS.cookie_pre+c;
    }
    document.cookie=c+"="+escape(d)+a+"; path=/";
}
if(!get_cookie("nickname")){
    setCookie("auth","",-1);
    setCookie("auth_wl","",-1);
    setCookie("uid","",-1);
    setCookie("nickname","",-1);
    setCookie("username","",-1);
    setCookie("own_room","",-1);
    setCookie("groupid","",-1);
    setCookie("notification","",-1);
}
$SYS.uid=get_cookie("uid");
$SYS.username=get_cookie("username");
$SYS.nickname=get_cookie("nickname");
$SYS.own_room=get_cookie("own_room");
$SYS.groupid=get_cookie("groupid");
$SYS.notification=parseInt(get_cookie("notification"));
function sync_login(c,e){
    if(!document.getElementById("sync_login")){
        var a=document.createElement("div");
        a.id="sync_login";
        a.style.display="none";
        document.body.appendChild(a);
    }
    sync_callback=e;
    setTimeout(sync_callback,2000);
    $("#sync_login").html(c);
    var d=$("#sync_login").children();
    sync_total=d.length;
    sync_finish=0;
    for(var b=0;b<d.length;b++){
        d[b].onload=function(){
            sync_finish++;
            if(sync_finish===sync_total){
                setTimeout(sync_callback,1);
            }
        }
    }
}
function get_url_param(a){
    a=a.replace(/[\[]/,"\\[").replace(/[\]]/,"\\]");
    var c=new RegExp("[\\?&]"+a+"=([^&#]*)"),b=c.exec(location.search);
    return b==null?"":decodeURIComponent(b[1].replace(/\+/g," "))
}
function timetodate(e){
    var d=new Date(e*1000);
    var c=d.getHours();
    c=c<10?"0"+c:c;
    var a=d.getMinutes();
    a=a<10?"0"+a:a;
    var b=d.getSeconds();
    b=b<10?"0"+b:b;
    return c+":"+a+":"+b;
}
function timetodate_all(d){
    var c=new Date(d*1000);
    var e=c.getMonth()+1;
    var b=c.getHours();
    b=b<10?"0"+b:b;
    var a=c.getMinutes();
    a=a<10?"0"+a:a;
    return c.getFullYear()+"-"+e+"-"+c.getDate()+" "+b+":"+a;
}
function is_email(a){
    var b=/^([a-zA-Z0-9]+[_|\-|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\-|\.]?)*[a-zA-Z0-9\-]+\.[a-zA-Z]{2,4}$/;
    return b.test(a);
}
function close_open(a){
    $.dialog.list.REG001.close();
    if(a){
        window.location.reload();
    }
}
function open_reg(){
    user_dialog.open_reg();
    return false;
}
var login_jump="";
function open_login(){
    if(typeof(arguments[0])!=="undefined"){
        login_jump=arguments[0];
    }
    user_dialog.open_login();
    return false;
}
function check_message(){
    if($SYS.uid){
        window.location.href="/member/message/release";
    }
    else{
        open_login("/member/message/release");
    }
    return false;
}
function feedback_copyright(){
    window.$feedback_copyright_dialog=artDialog.open("/feedback/copyright",{
        width:650,height:330
    },
    true);
}
var logout=function(){
    $.post("/member/logout/ajax",function(a){
        var b="";
        sync_login(a.sync_login_html+b,"window.location.reload();");
        try{
            thisMovie("WebRoom").js_userlogout();
        }
        catch(c){
            
        }
        $.dialog.tips_black("",1.5);
    },
    "json");
};
function logout_submit(){
    $.dialog.confirm("",logout);
}
function reg_success(a,b){
    if($.dialog.list.REG001){
        $.dialog.list.REG001.close();
    }
    if(b!==""){
        $.dialog({
            icon:"succeed",content:"!",lock:true
        });
        sync_login(b,"window.location.reload();");
    }
    else{
        window.location.reload();
    }
}
function search_submit(){
    var a=$("#search_word").val();
    a=$.trim(a);
    if(a===""){
        alert_msg("","$('#search_word').focus();");
        return false;
    }
    window.location.href="/search/"+encodeURIComponent(a);
}
function alert_msg(d,b,a){
    try{
        switch(a){
            case 4:case"succeed":var f="succeed";
            break;
            case 3:var f="error";
            break;
            case 2:var f="question";
            break;
            default:var f="warning"
        }
        $.dialog({
            lock:true,content:d,icon:f,ok:function(){
                b&&setTimeout(b,100);
                return true;
            }
        });
    }
    catch(c){
        $.dialog.tips_black(d);
        b&&setTimeout(b,100);
    }
}
function confirm_msg(c,d,a){
    try{
        $.dialog.confirm(c,function(){
            d&&setTimeout(d,100);
        },
        function(){
            a&&setTimeout(a,100);
        });
    }
    catch(b){
        if(confirm(c)){
            d&&setTimeout(d,100);
        }
        else{
            a&&setTimeout(a,100);
        }
    }
}
function getByteLen(c){
    var a=c.length;
    if(c.match(/[^\x00-\xff]/ig)!==null){
        var b=c.match(/[^\x00-\xff]/ig).length;
        a=a+b*2;
    }
    return a;
}
var bottom_tips={
    pos:function(){
        var a=$(window).width();
        if(a>=1164){
            var b=parseInt(a-1000)/2+1235;$("#tbox").css({
                left:b,bottom:10
            }).
            show();
        }
        else{
            $("#tbox").hide();
        }
    },
    move:function(){
        h=$(window).height()/4;t=$(document).scrollTop();if(t>h){$("#gotop").fadeIn("slow");
    }
    else{
        $("#gotop").fadeOut("slow");
    }
},
init:function(){
    $("body").append('<div id="tbox" style="left: 1461px; bottom: 10px;"><a id="gotop" href="javascript:void(0)"></a><a id="dj" href="/cms/zhibo/201407/07/281.shtml"  target="_blank"></a><a id="want" href="/cms/zhibo/list_16.shtml" target="_blank"></a><a id="jianyi"  href="javascript:void(0)" onclick="return check_message()"></a></div>');
    this.pos(10,10);
    this.move();
    $("#gotop").click(function(){
        $(document).scrollTop(0);
        return false;
    });
    $(window).resize(function(){
        bottom_tips.pos();
    });
    $(window).scroll(function(a){
        bottom_tips.move();
    });
}
};
function number_format(f,c,i,e){
f=(f+"").replace(/[^0-9+\-Ee.]/g,"");
var b=!isFinite(+f)?0:+f,a=!isFinite(+c)?0:Math.abs(c),k=(typeof e==="undefined")?",":e,d=(typeof i==="undefined")?".":i,j="",g=function(o,m){
    var l=Math.pow(10,m);
    return""+(Math.round(o*l)/l).toFixed(m)};j=(a?g(b,a):""+Math.round(b)).split(".");
    if(j[0].length>3){
        j[0]=j[0].replace(/\B(?=(?:\d{3})+(?!\d))/g,k);
    }
    if((j[1]||"").length<a){
        j[1]=j[1]||"";
        j[1]+=new Array(a-j[1].length+1).join("0");
    }
    return j.join(d);
}
function get_avatar(a,b){
    if(typeof($SYS.avatar_url)==="undefined"){
        return"";
    }
    if(!b){
        b="small";
    }
    return $SYS.avatar_url+"avatar.php?uid="+a+"&size="+b;
}
var loading={
    lock:false,dialog:null,show:function(a){
        if(!a){
            a="";
        }
        if(loading.dialog){
            loading.close();
        }
        loading.dialog=$.dialog({
            title:false,cancel:false,lock:loading.lock,content:'<div class="infodrmation"><img src="'+$SYS.res_url+'douyu/images/loading.gif" style="vertical-align: middle;" >&nbsp;'+a+"</div>"
        });
    },
    close:function(){
        if(loading.dialog){
            loading.dialog.close();
        }
    }
};
var user_dialog={
    _dialog:null,chg_tab:function(a){
        $("#js_login_tab a").removeClass("current");
        $("#js_"+a).addClass("current");
        $("#js_login_dialog .inputBox").hide();
        $("#js_"+a+"_cont").show();
    },
    open_login:function(){
        if($("#js_login_dialog").length<1){
            throw"dialog no found";
        }
        this.chg_tab("login");
        if($("#js_login_dialog").is(":hidden")){
            this.show();
        }
        $("#login-form").find("input[name='username']").focus();
    },
    open_reg:function(){
        if($("#js_login_dialog").length<1){
            throw"dialog no found";
        }
        this.chg_tab("reg");
        if($("#js_login_dialog").is(":hidden")){
            this.show();
        }
        $("#reg_form").find("input[name='nickname']").focus();
    },
    show:function(){
        user_dialog._dialog=$.dialog({
            content:document.getElementById("js_login_dialog"),title:false,cancel:false,padding:0,margin:0,fixed:true,lock:true
        });
        return false;
    },
    hide:function(){
        if(user_dialog._dialog){
            user_dialog._dialog.close();
        }
        return false;
    },
    logout:function(){
        $.dialog.confirm("",function(){
            $.post("/member/logout/ajax",function(a){
                try{
                    thisMovie("WebRoom").js_userlogout();
                }
                catch(b){
                    
                }
                $.dialog.tips_black("",1.5);
                window.location.reload();
            },
            "json");
        });
    }
};
var user_form={
    check:function(c){
        var b=$(c);
        var d=b.val();
        d=$.trim(d);
        b.val(d);
        if(d==""){
            inputError(b);
            return false;
        }
        switch(b.attr("name")){
            case"nickname":case"username":if(d==""){
                this.error("",b);
                return false;
            }
            if(d.indexOf("_")===0){
                this.error("",b);
                return false;
            }
            var a=this.get_byte_len(d);
            if(a<5||a>30){
                this.error("5~30",b);
                return false;
            }
            break;
            case"password":if(d.length<5||d.length>25){
                this.error("5~25",b);
                return false;
            }
            break;
            case"password2":if(b.parents("form").find("input[name='password']").val()!=d){
                this.error("",b);
                return false;
            }
            break;
            case"email":var e=/^([a-zA-Z0-9]+[_|_|.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|_|.]?)*[a-zA-Z0-9]+.[a-zA-Z]{2,4}$/;
            if(!e.test(d)){
                this.error("",b);
                return false;
            }
            break;
            case"captcha_word":if(d.length!=4){
                this.error("",b);
                return false;
            }
            break;
        }
        this.success(b);
        return true;
    },
    error:function(b,a){
        $.dialog.tips_black(b,2);
        inputError(a);
    },
    success:function(a){
        if(inputError.timer){
            clearTimeout(inputError.timer);
        }
        a.removeClass("login-form-error");
    },
    get_byte_len:function(c){
        var a=c.length;
        if(c.match(/[^\x00-\xff]/ig)!=null){
            var b=c.match(/[^\x00-\xff]/ig).length;
            a=a+b*2;
        }
        return a;
    },
    update_vcode:function(b){
        var a=$("#"+b).data("src")+"?_t="+Math.random(1);
        $("#"+b).attr("src",a);
        $("#"+b+"_val").val("");
    }
};
var inputError=function(a){
    clearTimeout(inputError.timer);
    var b=0;
    var c=function(){
        inputError.timer=setTimeout(function(){
            if(!a.hasClass("login-form-error")){
                a.addClass("login-form-error");
            }
            if(b>=5){
                a.removeClass("login-form-error");
            }
            else{
                c(b++);
            }
        },
        300);
    };
    c();
};
var doing=0;
function reg_ajaxSubmit(){
    if(doing==1){
        return false;
    }
    var a=true;
    $("#reg_form input").each(function(){
        var b=$(this).attr("type");
        if(b!="submit"&&b!="hidden"&&!$(this).hasClass("placeholder")&&user_form.check(this)==false){
            a=false;
            return false;
        }
    });
    if(!a){
        return false;
    }
    doing=1;
    $("#js_reg_submit").val("");
    $.ajax({
        type:"POST",url:"/member/register/ajax",data:$("#reg_form").serialize(),dataType:"json",error:function(b,d,c){
            $.dialog.tips_black("");
        },
        success:function(b){
            doing=0;
            $("#js_reg_submit").val("");
            if(b.result==0){
                $("#culp a").trigger("click");
                $.dialog.tips_black("",1.5);
                window.location.reload();
            }
            else{
                user_form.update_vcode("reg_captcha");
                $.dialog.tips_black(""+b.error);
            }
        }
    });
    return false;
}
function login_ajaxSubmit(a){
    if(doing==1){
        return false;
    }
    var b=true;
    $("#login-form input").each(function(){
        var c=$(this).attr("type");
        if(c!="submit"&&c!="hidden"&&!$(this).hasClass("placeholder")&&user_form.check(this)==false){
            b=false;
            return false;
        }
    });
    if(!b){
        return false;
    }
    doing=1;
    $("#js_login_submit").val("");
    $.post("/member/login/ajax",$("#login-form").serialize(),function(c){
        doing=0;
        $("#js_login_submit").val("");
        if(c.result==0){
            $("#culp a").trigger("click");
            if(typeof(a)==="function"){
                a();
            }
            else{
                $.dialog.tips_black("",1.5);
                if(typeof(login_jump)!="undefined"&&login_jump){
                    window.location.href=login_jump;
                }
                else{
                    window.location.reload();
                }
            }
        }
        else{
            switch(c.result){
                case -1:var d="";
                break;
                case -2:var d="";
                break;
                case -3:var d="";
                break;
                case -5:var d="";
                break;
                case -4:if(c.ban_time==0){
                    var d="";
                }
                else{
                    var d=""+c.ban_time;
                }
                break;
                case -99:var d="";
                break;
                default:var d=c.result
            }
            user_form.update_vcode("login_captcha");
            $.dialog.tips_black(d);
        }
    },
    "json");
    return false;
}
function get_his_time(c,b){
    var a=c-b;
    if(a>=604800){
        return"";
    }
    if(a>=86400){
        return Math.floor(a/86400)+"";
    }
    if(a>=3600){
        return Math.floor(a/3600)+"";
    }
    if(a>=1200){
        return Math.floor(Math.floor(a/60)/15)*15+"";
    }
    if(a>=900){
        return"15";
    }
    if(a>=60){
        return Math.floor(a/60)+"";
    }
    return"";
}
function get_show_online(a){
    a=parseInt(a);
    if(a<1){
        return 0;
    }
    if(a>=10000){
        return(a/10000).toFixed(1)+"";
    }
    else{
        return a;
    }
}
function notification_bubble(b){
    setCookie("notification",b);
    var a=$(".notification_bubble b");
    if(a.length){
        if(b>0){
            a.html(b);
        }
        else{
            a.remove();
        }
    }
    else{
        if(b>0){
            $(".notification_bubble").append("<b>"+b+"</b>");
        }
    }
}
function home_mobile_notice(){
    if(/AppleWebKit.*Mobile/i.test(navigator.userAgent)||(/MIDP|SymbianOS|NOKIA|SAMSUNG|LG|NEC|TCL|Alcatel|BIRD|DBTEL|Dopod|PHILIPS|HAIER|LENOVO|MOT-|Nokia|SonyEricsson|SIE-|Amoi|ZTE/.test(navigator.userAgent))){
        try{
            $SYS.is_mobile=true;
            if(/Android|webOS|iPhone|iPod|BlackBerry/i.test(navigator.userAgent)){
                if(window.screen.width<=640){
                    
                }
            }
            else{
                if(/iPad/i.test(navigator.userAgent)){
                    
                }
                else{
                    
                }
            }
        }
        catch(a){
            
        }
    }
}
if(location.pathname=="/"){
    home_mobile_notice();
}
$(document).ready(function(b){
    if($("body").data("page")=="home"){
        bottom_tips.init();
    }
    else{
        $(".js_index_but").removeClass("current");
    }
    $("input, textarea").placeholder();
    $(".js_live_setup,.js_his,#headfolow").hide();
    if($SYS.uid){
        $(".js_login_no").hide();
        $(".js_nickname").html($SYS.nickname);
        $(".js_avatar").attr("src",get_avatar($SYS.uid));
        $("#left_big_show").css({
            top:185
        });
        if($SYS.own_room==="1"){
            $(".js_member_url").attr("href","/room/my");
            $(".js_login_room,.js_live_setup").show();
        }
        else{
            $(".js_login_member").show();
        }
        $(".js_login_yes").show();
        $(".js_his,#headfolow").show();
        if($SYS.groupid==="5"){
            $(".js_login_sa").show();
        }
    }
    else{
        $(".js_login_yes, .js_login_member, .js_login_room, .js_login_sa").hide();
        var a=window.location.hash;
        if(a&&a.substr(1)==="dy_tool_reg"){
            user_dialog.open_reg();
        }
    }
    $(".js_head_menu").bind("mouseleave",function(c){
        if($("body").data("page")=="home"){
            $(".js_index_but").addClass("current");
        }
    });
    $(".js_search_txt").focus(function(){
        $(".js_search").animate({
            width:"140px"
        },
        300);
        $(".js_search_txt").animate({
            width:"102px"
        },
        300);
    });
    $(".js_search_txt").blur(function(){
        if($(this).val().length==0){
            $("#search_word").attr("placeholder","/");
        }
        $(".js_search").animate({
            width:"116px"
        },
        300);
        $(".js_search_txt").animate({
            width:"78px"
        },
        300);
    });
    $("#js_head_game,#js_member_pic").mouseleave(function(){
        var c=$(this).find(".js_head_show").eq(0);
        c.finish();
        if($(this).data("arrow")){
            $("."+$(this).data("arrow")).removeClass($(this).data("css"));
        }
        c.slideUp("fast");
    });
    $("#js_head_game,#js_member_pic").mouseover(function(){
        var c=$(this).find(".js_head_show").eq(0);
        c.finish();
        if($(this).data("arrow")){
            $("."+$(this).data("arrow")).addClass($(this).data("css"));
        }
        c.slideDown("fast");
        return false;
    });
    $("#headfolow").mouseleave(function(){
        $("#folowdiv").finish();
        $("#folowdiv").slideUp("fast");
        $("#follow_sj").removeClass("his_up");
        if($("#js_myfollow").data("stat")==2){
            $("#js_myfollow").data("stat",0);
            $("#followlist").html("");
            $("#loadfollow").hide();
        }
    });
    $("#js_myfollow").mouseover(function(){
        if(!$SYS.uid){
            return false;
        }
        $("#folowdiv").finish();
        $("#folowdiv").slideDown("fast");
        $("#follow_sj").addClass("his_up");
        if($(this).data("stat")==0){
            $("#loadfollow").show();
            $("#followlist").html("");
            $("#nofollow").hide();
            $(this).data("stat",1);
            $.ajax({
                type:"POST",url:"/member/cp/get_follow_list",dataType:"json",success:function(d){
                    $("#js_myfollow").data("stat",2);
                    $("#loadfollow").hide();
                    var c="";
                    $.each(d.room_list,function(f,i){
                        c+='<li class="li1"><p><a href="/'+i.room_id+'"  target="_blank">'+i.room_name+"</a></p>";
                        var g=parseInt((d.nowtime-i.show_time)/60);c+='<span><a href="/'+i.room_id+'" class="head_icon1"   target="_blank">'+g+"</a> ";
                        c+='<a href="'+i.room_id+'" class="head_icon2"   target="_blank">'+i.nickname+"</a>";
                        c+='<a href="'+i.room_id+'" class="head_icon3"   target="_blank">'+get_show_online(i.online)+"</a> ";
                        c+="</span></li>";
                    });
                    if(c==""){
                        var e=parseInt(d.nolive)>0?"":"";
                        $("#nofollow").html(e);
                        $("#nofollow").show();
                    }
                    else{
                        $("#followlist").html(c);
                    }
                }
            });
        }
        return false;
    });
    $(".js_his").mouseleave(function(){
        $(".js_his_list").finish();
        $(".js_his_list").slideUp("fast");
        $("#his_sj").removeClass("his_up");
        if($(".js_header_his").data("stat")==2){
            $(".js_header_his").data("stat",0);
            $(".js_his_list ul").html("");
            $("#loadhis").hide();
        }
    });
    $(".js_header_his").mouseover(function(){
        if(!$SYS.uid){
            return false;
        }
        $(".js_his_list").finish();
        $(".js_his_list").slideDown("fast");
        $("#his_sj").addClass("his_up");
        if($(this).data("stat")==0){
            $("#loadhis").show();
            var c=$(".js_his_list ul");
            c.html("");
            $(this).data("stat",1);
            $(".js_no_his").hide();
            $.ajax({
                type:"POST",url:"/member/cp/get_user_history",dataType:"json",success:function(e){
                    $(".js_header_his").data("stat",2);
                    $("#loadhis").hide();
                    var f=e.nowtime;
                    var d="";
                    $.each(e.history_list,function(g,i){
                        i.n=$.trim(i.n);
                        d+='<li class="li1"><p><a href="/'+i.rid+'" target="_blank">'+(i.n!=""?i.n:"&nbsp;&nbsp;")+'</a></p><span><a href="javascript:void(0);" class="';
                        d+=i.ls==0?"head_icon4":"head_icon1";
                        d+='">';
                        d+=get_his_time(e.nowtime,i.lt)+'</a><a href="javascript:void(0);" class="head_icon2">'+i.on+"</a>";
                        d+='<a href="javascript:void(0);" class="head_icon3">'+get_show_online(i.uc)+"</a></span></li>";
                    });
                    if(d==""){
                        $(".js_no_his").show();
                    }
                    else{
                        c.html(d);
                    }
                }
            });
        }
        return false;
    });
    $("#culp a").click(user_dialog.hide);
    $("#login_captcha, #reg_captcha").click(function(){
        user_form.update_vcode($(this).attr("id"));
    });
    $("#login_captcha_val, #reg_captcha_val").focus(function(){
        var c=$(this).next();
        if(c.attr("src").indexOf("captcha")==-1){
            c.trigger("click");
        }
    });
    $("#js_login, #js_reg").click(function(){
        if($(this).attr("id")=="js_login"){
            user_dialog.open_login();
        }
        else{
            user_dialog.open_reg();
        }
        return false;
    });
    $("#reg_form").submit(reg_ajaxSubmit);
    $("#reg_form input").each(function(){
        if($(this).attr("type")!=="submit"&&$(this).attr("type")!=="hidden"&&!$(this).hasClass("placeholder")){
            $(this).blur(function(){
                if(user_form.check(this)){
                    var c=$(this).attr("name");
                    var e=$(this);
                    if(c=="nickname"){
                        doing=1;
                        $.post("/member/register/validate/nickname","data="+encodeURIComponent(e.val()),function(g){
                            doing=0;
                            if(g.result==0){
                                user_form.success(e);
                            }
                            else{
                                if(g.result==-2){
                                    user_form.error("",e);
                                }
                                else{
                                    user_form.error("",e);
                                }
                            }
                        },
                        "json");
                    }
                    else{
                        if(c=="email"){
                            var f=$.trim(e.val());
                            var d=/\@(vip\.)?qq\.com$/i;
                            if(!d.test(f)){
                                user_form.error("QQ",e);
                                return false;
                            }
                            doing=1;
                            $.post("/member/register/check_email","email="+encodeURIComponent(e.val()),function(g){
                                doing=0;
                                if(g.result==0){
                                    user_form.success(e);
                                }
                                else{
                                    user_form.error("",e);
                                }
                            },
                            "json");
                        }
                    }
                }
            });
        }
    });
    $("#login-form").submit(login_ajaxSubmit);
    $("#login-form input").each(function(){
        if($(this).attr("type")!=="submit"&&$(this).attr("type")!=="hidden"&&!$(this).hasClass("placeholder")){
            $(this).blur(function(){
                user_form.check(this);
            });
        }
    });
    if(typeof $SYS.is_mobile=="boolean"&&$SYS.is_mobile){
        $("body").append('<div id=\'mobile_notice_box\' class=\'hidden\'><div class="box_cont"><a href="/client/jump" class="box_word"><span>TV</span></a></div><a href="/client/jump" class="box_btn"></a><div class="box_pic"></div></div>');
        $("#banner").remove();
        $("#mobile_notice_box .box_pic").click(function(){
            $("#mobile_notice_box").slideUp("fast",function(){
                $(this).remove();
            });
        });
    }
    else{
        $("#mobile_style_elem").remove();
    }
    if($SYS.notification>0){
        notification_bubble($SYS.notification);
    }
});
