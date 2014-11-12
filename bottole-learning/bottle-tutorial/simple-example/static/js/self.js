

//对错误信息进行处理，
//如果没有错误信息，则隐藏错误label
//如果有，则显示，并且加上特殊标识
function validate_errorinfo(){
    $('label.error-info').each(function(){
        var error_text=$(this).text();

        if(!error_text){
            $(this).hide();
        }
        else{
            $(this).show();
            $(this).parents('.form-group').filter(function(){
               return  $(this).parent().is('form');
            }).addClass('has-error');
        }
    });
    $('input').focus(function(){
        $(this).parents('.form-group').filter(function(){
            return $(this).parent().is('form');
        }).removeClass('has-error')
            .find('label.error-info').hide();

    });
}

//添加日期插件

//全选功能的JS块
$("td.tdwraper .cellinner").click(
    function(e){
        e.stopPropagation();
    }
);


 $(".tdwraper").click(function() {

     var $checkbox = $(this).find('input[type=checkbox]');
     var checkvalue = $checkbox.attr("checked") || false;
     $checkbox.attr("checked",!checkvalue);
     $checkbox.click();
     $checkbox.attr("checked",!checkvalue);
 });



$("th.thwraper .cellinner").click(function(e){
    e.stopPropagation();
    var th_checkvalue=$(this).attr('checked')||false;
    $(this).closest('table').find('td.tdwraper .cellinner').attr("checked",th_checkvalue);
});


$('th.thwraper').click(function(){
    $("#chk_all").attr('checked',!$("#chk_all").attr('checked')||false);
   $(this).find('.cellinner').click();
   $("#chk_all").attr('checked',!$("#chk_all").attr('checked')||false);
});



//一些基本的处理
function get_url_exclude_parameter(input_url){
    //获取URL并且去除后面的参数
    return input_url.split('?')[0];
}



//删除功能的JS块
$(".listaction").click(function(e){
    e.stopPropagation();
    var td_checkbox_cls=$(this).attr('td-checkbox');//checkbox所在td的样式
    var td_id_cls=$(this).attr('td-id-cls');//要传送的主键所在td的样式
    var base_url=get_url_exclude_parameter($(this).attr('remote')); //请求的网址
    var $this_table=$("table."+$(this).attr("table-class"));

    var $checked_ids=$this_table.find("."+td_checkbox_cls+"  input[type=checkbox]:checked").closest('tr')
        .find("."+td_id_cls);

    var arrayobj=new Array();

    for(var i=0;i<$checked_ids.length;i++){
        arrayobj.push($($checked_ids[i]).text());
    }

    var final_url=base_url+"?ids=["+arrayobj.join(',')+"]";
    $.get(final_url,function(data){
        window.location.href=data;
    });

});



validate_errorinfo();

