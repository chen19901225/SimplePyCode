 +function($){

     var FormModal=function(element,options){
       this.$element=$(element);
       this.super=this.$element.data('bs.modal');
       this.options=options;

       this.$element.on('click.submit.formodal','[data-form="submit"]', $.proxy(this.submit,this));
       this.$element.on('click.reset.formmodal','[data-form="reset"]', $.proxy(this.reset,this));
       this.$element.on('click.cancel.formmodal','[data-form="cancel"]', $.proxy(this.cancel,this));

       var that=this;

       this.$element.on('show.bs.modal',function(e){
           that.$element.trigger(e= $.Event('show.bs.formmodal'));
           if(e.isDefaultPrevented()) return;
       });

       this.$element.on('shown.bs.modal',function(e){
           that.$form=that.$element.find('form');
           that.$element.trigger(e= $.Event('shown.bs.formmodal'));
           if(e.isDefaultPrevented()) return;

       });

       this.$element.on('hide.bs.modal',function(e){
           that.$element.trigger(e= $.Event('hide.bs.formmodal'));
           if(e.isDefaultPrevented()) return;
       });

       this.$element.on('hidden.bs.modal',function(e){
           that.$element.trigger(e= $.Event('hidden.bs.formmodal'));
           if(e.isDefaultPrevented()) return;
       });

     };

     FormModal.DEFAULTS={
         cacheForm:false,
         closeAfterCancel:true
     };

     FormModal.prototype.toggle=function(_relatedTarget){
       return this[!this.super.isShown?'show':'hide'](_relatedTarget);
     };
     FormModal.prototype.show=function(_relatedTarget){
         this.super.show(_relatedTarget);
     };

     FormModal.prototype.hide=function(e){
         if(e) e.preventDefault();
         this.super.hide();
     }

     FormModal.prototype.submit=function(e){
       if(e) e.preventDefault();

         this.$element.trigger(e= $.Event('beforeSubmit.bs.formmodal'));

         if(e.isDefaultPrevented()) return;
         var that=this;
         //this.$form.submit();
         var post_data=this.$form.serialize();
        // $.post(this.$form[0].action,post_data,function(data){
          //  that.$element.empty.html(data);
        // });

        // if(this.$form.jqBootstrapValidation&&this.$form.jqBootstrapValidation()!=true)
         //return false;



         $.ajax({
             url:this.$form[0].action,
             data:post_data,
             async:false,
             type:"POST",
             success:function(data){
             that.$element.find(".modal-content").empty().html(data);
         }

         });



         this.$element.trigger(e= $.Event('afterSubmit.bs.formmodal'));

         if(e.isDefaultPrevented()) return;
     };

     FormModal.prototype.reset=function(e){
         if(e) e.preventDefault();

         var resetAction=function(){
             this.$element.trigger(e= $.Event('beforeReset.bs.formmodal'));

             if(e.isDefaultPrevented()) return;
             this.$form.each(function(){
                 this.reset();
             });

             this.$element.trigger(e= $.Event('afterReset.bs.formmodal'));

             if(e.isDefaultPrevented()) return;
         };

         if(this.super.isShown) return resetAction.call(this);

         this.$element.one('shown.bs.formmodal', $.proxy(resetAction,this));
         this.show();
     };

     FormModal.prototype.cancel=function(e){
         if(e) e.preventDefault();

         var e= $.Event('cancel.bs.formmodal');
         this.$element.trigger(e);

         if(e.isDefaultPrevented()) return;
         if(this.options.closeAfterCancel){
             this.hide(e);
         }
     };

     var old= $.fn.formmodal;

     $.fn.formmodal=function(option,_relatedTarget){
         return this.each(function(){
             var $this=$(this);
             var options= $.extend({},FormModal.DEFAULTS,$this.data(),
             typeof option=='object'&&option);

             var data=options.cacheForm&&$this.data('bs.formmodal');

             options.show=false;

             if(!options.cacheForm){
                 $this.data('bs.modal',null);
             }

             $this.modal(options,_relatedTarget);

             if(!data) $this.data('bs.formmodal',(data=new FormModal(this,options)));

             if(typeof  options=='string'){
                 data[option](_relatedTarget);
             }else{
                 data.show(_relatedTarget);
             }

         });
     };

     $.fn.formmodal.Constructor=FormModal;

     $.fn.formmodal.noConflict=function(){
         $.fn.formmodal=old;
         return this;
     };

     $(document).on('click.bs.formmodal.data-api','[data-toggle="formmodal"]',function(e){
         var $this=$(this);
         var href=$this.attr('href');

         var $target=$($this.attr('data-target')||
             (href&&href.replace(/.*(?=#[^\s]+$)/,'')));

         var option=$target.data('formodal')?'toggle': $.extend({
             remote:!/#/.test(href)&&href         },$target.data(),$this.data());

         e.preventDefault();
         $target.formmodal(option,this)
             .one('hide',function(){
                 $this.is(':visible')&&$this.focus();
             });
     });
 }(jQuery)