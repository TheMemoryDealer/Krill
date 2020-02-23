"use strict";

function trip_change() {
    $("#gallery tbody").empty();
    var url = $("#trip_list").attr("ajax-url"); // gets text contents of clicked li
    $.ajax({
        type: "POST",
        url: url,
        data: {
            trip_to_get: $('#trip_list').val(),
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")
        },
        success: function (result) {
            $("#alt-view").empty()
            var image_list = result['trip_image_list'];
            for(var i = 0; i < image_list.length; i++){
                
                $("#gallery tbody").prepend(
                    "<tr><td>"+ image_list[i]+" </td></tr>"
                  )
                  $("#alt-view").prepend(
                    "<option value="+ image_list[i]+">"+image_list[i]+"</option>"
                  )
                
            }
            $("#alt-view").append(
                "<option value=></option>"
              )
              $("#alt-view").append(
                "<option value=NONE>NONE</option>"
              )
           
        }
    })


};


function asd() {
    var csvline = [];
    var csvArray= [];

    var csvlineAttributes = [];
    var csvArrayAttributes= [];
    var region_ids = [];

    for ( var image_id in _via_img_metadata ) { 
        var r = _via_img_metadata[image_id].regions;
        if ( r.length !==0 ) {
          for ( var i = 0; i < r.length; ++i ) {
            // Shape attributes are HERE.
            var sattr = map_to_json( r[i].shape_attributes );
            csvline.push(sattr);

            // Region Attributes
            var rattr = map_to_json( r[i].region_attributes );
            rattr = '"' +  escape_for_csv( rattr ) + '"';
            csvlineAttributes.push(r[i].region_attributes);
            region_ids.push(r[i].region_id);
          }
        }
      }
      if(csvlineAttributes.length != 0){
          csvArrayAttributes = csvlineAttributes;
            csvlineAttributes = JSON.stringify(csvlineAttributes);
      }
      else{
          csvlineAttributes = "";
      }

      if(csvline.length != 0){
        csvArray = csvline;
        csvline = JSON.stringify(csvline);
    }
    else{
        csvline = "";
    }
    var image = document.getElementById("current_image").innerHTML;
    
    image = image.replace($("#delete_photo").attr("media-url"),"");
    
    // Removes whitespace
    image = image.trim();
    console.log(image)
    $.ajax({
        type: "POST",
        url: "/via/alt",
        data: {
            image_file: image,
            alt_img: $("#alt-view").val(),
            krill_attributes: JSON.stringify(csvArray),
            region: JSON.stringify(region_ids),
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")
        },
        success: function (result) {
            console.log(JSON.stringify(csvArray))
            console.log($("#alt-view").val())
        }
    })
}

function user_click_image(path){
    _via_img_metadata={};
    var img_id    = project_file_add_url(path);
    $.ajax({type: "GET",
        url: '/via/microdata',
        data: {image: img_id,
                'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")},
    success:function(result){
        document.getElementById("board").value = result.board
        document.getElementById("event").value = result.net
        document.getElementById("netbox").value = result.event
        document.getElementById("alt-view").value = result.altr_view
        let xyz = result.position;
        console.log(xyz)
        console.log(result.altr_view)
        if (xyz == "Lateral"){
            let a = "Dorsal"
            document.getElementById("pbox").value = result.position
            $("#picname").text(a + " view:");
        }
        else if (xyz == "Dorsal"){
            let a = "Lateral"
            document.getElementById("pbox").value = result.position
            $("#picname").text(a + " view:");
        }
        else{
            document.getElementById("pbox").value = ""
            $("#picname").text("Alternative view:");
        }

    }})
    var img_index = _via_image_id_list.indexOf(img_id);
    _via_show_img(img_index);
}


function save_annotations_to_DB(){
    var csvline = [];
    var csvArray= [];

    var csvlineAttributes = [];
    var csvArrayAttributes= [];
    var region_ids = [];

    for ( var image_id in _via_img_metadata ) { 
        var r = _via_img_metadata[image_id].regions;
        if ( r.length !==0 ) {
          for ( var i = 0; i < r.length; ++i ) {
            // Shape attributes are HERE.
            var sattr = map_to_json( r[i].shape_attributes );
            csvline.push(sattr);

            // Region Attributes
            var rattr = map_to_json( r[i].region_attributes );
            rattr = '"' +  escape_for_csv( rattr ) + '"';
            csvlineAttributes.push(r[i].region_attributes);
            region_ids.push(r[i].region_id);
          }
        }
      }
      if(csvlineAttributes.length != 0){
          csvArrayAttributes = csvlineAttributes;
            csvlineAttributes = JSON.stringify(csvlineAttributes);
      }
      else{
          csvlineAttributes = "";
      }

      if(csvline.length != 0){
        csvArray = csvline;
        csvline = JSON.stringify(csvline);
    }
    else{
        csvline = "";
    }



      var image = document.getElementById("current_image").innerHTML;
      image = image.replace($("#delete_photo").attr("media-url"),"");
      // Removes whitespace
      image = image.trim();

    var url = $("#save_annotations").attr("ajax-url"); // gets text contents of clicked li
        console.log($("#alt-view").val())
        if ($("#alt-view").val() == ''){
            $.alert({
                title: 'Please connect alternate image first',        
                content: ''
            });
        }
        $.ajax({
            type: "POST",
            url: url,
            data: {
                image_file: image,
                image_annotations: JSON.stringify(csvArray),
                krill_attributes: csvlineAttributes,
                board: $("#board").val(),
                event: $("#event").val(),
                alt_img: $("#alt-view").val(),
                net: $("#netbox").val(),
                position: $("#pbox").val(),
                region: JSON.stringify(region_ids),
                'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")
            },
            success: function (result) {
                    $.alert({
                        title: 'Save Data',
                        content: "Data Saved!",
                
                    });

               
            },
            error: function (result) {
                $.alert({
                    title: 'Something went wrong',
                    content: "Have you turned Toggle Annotations on ?",
            
                });

           
        },
            

        })

    
   




}

function detect_krill(){
    sel_all_regions();
    console.log("HEY!!!!!!");
    del_sel_regions();
    var image_file = document.getElementById("current_image").innerHTML;
    image_file = image_file.trim();

    var url = $("#detect_krill").attr("ajax-url");

    $.ajax({type: "POST",
    url: url,
    data: {image_file: image_file,
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")},
    success:function(result){

        var annotations = result['annotations'];                
        // Maps key (height, width, name) to value
        for ( var i = 0; i < annotations.length; i++ ) {
            var region_i = new file_region();
            var line = annotations[i];
            region_i.shape_attributes = line;
            region_i.region_attributes['Length'] = 0;
            region_i.region_attributes['Maturity'] = "Unclassified";


            for ( var image_id in _via_img_metadata ) {
            _via_img_metadata[image_id].regions.push(region_i);
            }

        }
        // Display annotations on image
        update_attributes_update_panel();
        annotation_editor_update_content();
        _via_load_canvas_regions(); // image to canvas space transform
        _via_redraw_reg_canvas();
        _via_reg_canvas.focus();
        
        

}

})


}

function toggleClicked(){

    sel_all_regions();
    del_sel_regions();
    var image_file = document.getElementById("current_image").innerHTML;
    image_file = image_file.trim();
    var url = $("#toggle_annotations").attr("ajax-url");

    var image = document.getElementById("current_image").innerHTML;

    image = image.replace($("#delete_photo").attr("media-url"),"");
    // Removes whitespace
    image = image.trim();
    // console.log(url)
    // console.log("u aint shit")
    $.ajax({type: "POST",
    url: url,
    data: {image_file: image_file,
            image: image,
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")},
    success:function(result){
   

        var annotations = result['annotations'];
        // console.log(annotations)
        var region_attributes = result['region_attributes'];
        //console.log(region_attributes)
        if(annotations!=""){
        var m = json_str_to_map( annotations );
        var r = json_str_to_map(region_attributes);

        // Maps key (height, width, name) to value
        for ( var i = 0; i < m.length; i++ ) {
            var region_i = new file_region();
            var bounding_box=r[i]['image_annotation'];
            var length=r[i]['length'];
            var maturity=r[i]['maturity'];
            
            bounding_box=bounding_box.replace(/\\/g, '');
            // console.log(bounding_box)
            region_i.shape_attributes = JSON.parse(bounding_box);
            region_i.region_attributes['Length']=length;
            region_i.region_attributes['Maturity']=maturity;

            for ( var image_id in _via_img_metadata ) {
            _via_img_metadata[image_id].regions.push(region_i);
            }

        }
        // Display annotations on image
        attribute_update_panel_set_active_button();
        update_attributes_update_panel();
        annotation_editor_update_content();
        _via_load_canvas_regions(); // image to canvas space transform
        _via_redraw_reg_canvas();
        _via_reg_canvas.focus();
        
        

    }
}

})

}

function delete_photo(){
    var image_to_delete= document.getElementById("current_image").innerHTML;

    // If there there is something to delete
    if (image_to_delete != null){

        var url = $("#delete_photo").attr("ajax-url");
    // Removes the django media URL from the URL.
    var media_url = image_to_delete.replace($("#delete_photo").attr("media-url"),"");
    // Removes whitespace
    media_url = media_url.trim();
    // Removes image from panel
    $("#image_panel img").remove();
    $("#current_image").empty();
    _via_update_ui_components();


 

    $.ajax({type: "POST",
    url: url,
    data: {image_url: media_url,
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")},
    success:function(result){
        trip_change();

    }})
        
    }
    

}

function pull_from_csv(){
    var image_to_pull= document.getElementById("current_image").innerHTML;
    image_to_pull = image_to_pull.replace($("#delete_photo").attr("media-url"),"");
    console.log(image_to_pull);
    image_to_pull = image_to_pull.trim();
    if (image_to_pull != null){
    $.ajax({type: "POST",
    url: "/pull_from_csv/",
    data: {image: image_to_pull,
            'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")},
    success:function(result){
        $.alert({
            title: 'Summary',
            content: result['num_pulled']+ " rows pulled from csv file.",
            buttons:{
                OK: function(){

        	    $('#toggle_annotations').bootstrapToggle('toggle');
        		$('#toggle_annotations').bootstrapToggle('toggle');
                }
            }
    
        });
    }})
        
    }
}




function sort_boxes(){
      var csvline = [];
    var csvArray= [];

    var csvlineAttributes = [];
    var csvArrayAttributes= [];
    var region_ids = [];

    for ( var image_id in _via_img_metadata ) {
        var r = _via_img_metadata[image_id].regions;
        if ( r.length !==0 ) {
          for ( var i = 0; i < r.length; ++i ) {
            // Shape attributes are HERE.
            var sattr = map_to_json( r[i].shape_attributes );
            csvline.push(sattr);

            // Region Attributes
            var rattr = map_to_json( r[i].region_attributes );
            rattr = '"' +  escape_for_csv( rattr ) + '"';
            csvlineAttributes.push(r[i].region_attributes);
            region_ids.push(r[i].region_id);
          }
        }
      }
      if(csvlineAttributes.length != 0){
          csvArrayAttributes = csvlineAttributes;
            csvlineAttributes = JSON.stringify(csvlineAttributes);
      }
      else{
          csvlineAttributes = "";
      }

      if(csvline.length != 0){
        csvArray = csvline;
        csvline = JSON.stringify(csvline);
    }
    else{
        csvline = "";
    }
     var image = document.getElementById("current_image").innerHTML;
      image = image.replace($("#delete_photo").attr("media-url"),"");
      // Removes whitespace
      image = image.trim();
    $.ajax({
            type: "POST",
            url: "/sort_boxes/",
            data: {
                image_file: image,
                image_annotations: JSON.stringify(csvArray),
                'csrfmiddlewaretoken': document.getElementById('trip_list').getAttribute("data-token")
            },
            success: function (result) {
                sel_all_regions();
                del_sel_regions();

                 var annotations = result['annotations'];
        // Maps key (height, width, name) to value
        for ( var i = 0; i < annotations.length; i++ ) {
            var region_i = new file_region();
            var line = annotations[i];
            region_i.shape_attributes = line;
            region_i.region_attributes['Length'] = 0;
            region_i.region_attributes['Maturity'] = "Unclassified";


            for ( var image_id in _via_img_metadata ) {
            _via_img_metadata[image_id].regions.push(region_i);
            }

        }
        // Display annotations on image
        update_attributes_update_panel();
        annotation_editor_update_content();
        _via_load_canvas_regions(); // image to canvas space transform
        _via_redraw_reg_canvas();
        _via_reg_canvas.focus();

            }
        })

}


$( document ).ready(function() {
    _via_attributes['region']['Length'] = {type: "text",description:"",default_value:""};
    _via_attributes['region']['Maturity'] = {type: "text",description:"",default_value:""};
    var rattr_id_list = Object.keys(_via_attributes['region']);
    _via_attribute_being_updated = 'region';
    _via_current_attribute_id = rattr_id_list[0];
    //rattr_count = 2;
    attribute_update_panel_set_active_button();
    update_attributes_update_panel();
    annotation_editor_update_content();

});





