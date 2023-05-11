

$(document).ready(function() {
  var witTipToggled = false;
  var protTipToggled = false;
  var modTipToggled = false;
  var assTipToggled = false;


  $("#toggleTeamsTip").click(function() {
    if (modTipToggled){
      $("#teamsTip").addClass("hidden");
      modTipToggled = false;

    }
    else{
      $("#teamsTip").removeClass("hidden");
      modTipToggled = true;
    }
  });


    
  $("#toggleTeamsTip2").click(function() {
    if (modTipToggled){
      $("#teamsTip2").addClass("hidden");
      modTipToggled = false;

    }
    else{
      $("#teamsTip2").removeClass("hidden");
      modTipToggled = true;
    }
  });




  $("#toggleAssTip").click(function() {
    if (assTipToggled){
      $("#assTip").addClass("hidden");
      assTipToggled = false;
    }
    else{
      $("#assTip").removeClass("hidden");
      assTipToggled = true;
    }
  });

  $("#toggleWitTip").click(function() {
    if (witTipToggled){
      $("#witTip").addClass("hidden");
      witTipToggled = false;
    }
    else{
      $("#witTip").removeClass("hidden");
      witTipToggled = true;
    }
  });


  $("#toggleModTip").click(function() {
    if (modTipToggled){
      $("#modTip").addClass("hidden");
      modTipToggled = false;

    }
    else{
      $("#modTip").removeClass("hidden");
      modTipToggled = true;
    }
  });

  $("#toggleProtTip").click(function() {
    if (protTipToggled){
      $("#protTip").addClass("hidden");
      protTipToggled = false;

    }
    else{
      $("#protTip").removeClass("hidden");
      protTipToggled = true;
    }
  });

  $("#killCamAdd").click(function() {
    $('#killCamYes').prop("checked", true);
  });



  $(".killAdd").click(function() {

    $('#killM').val($(this).parent().find(".method").text());

    // if ($('#killM').val() != "" ){
    // }
  });

  $(".safetyAdd").click(function() {
    if ($('#safetyCircs').val()!=""){
      $('#safetyCircs').val($('#safetyCircs').val()+", " + $(this).parent().find(".sugg").text());
    }
    else{
      $('#safetyCircs').val($(this).parent().find(".sugg").text());


    }

  });


  $("#extshow").click(function() {
    $('.extshow').removeClass("hidden");

  });

  $("#exthide").click(function() {

    $('.extshow').addClass("hidden");
    $('#extext').val("");

  });

  $("#limityes").click(function() {
    $('#hideLimitNum').removeClass("hidden");
  });

  $("#limitno").click(function() {
    $('#hideLimitNum').addClass("hidden");
  });

  $("#teams1").click(function() {
    $('#teamJoinMethod').addClass("hidden");
  });

  $("#teams2").click(function() {
    $('#teamJoinMethod').removeClass("hidden");
  });

  $("#teams3").click(function() {
    $('#teamJoinMethod').removeClass("hidden");
  });

  $("#teams4").click(function() {
    $('#teamJoinMethod').removeClass("hidden");
  });




  $("#defaultSettings").click(function() {

    $('#wityes').prop("checked", true);
    $('#safetyCircs').val("during class / work, while sleeping in bed");
    $('#killCamNo').prop("checked", true);
    $('#limitno').prop("checked", true);
    $('#killMethodHide').addClass("hidden");
    $('#killM').val("Touch a sock to target (the sock can be thrown or tapped on the body of target)");
    $('#exthide').prop("checked", true);
    $('#extext').val("");
    $('#email').prop("checked", true);
    $('#hideLimitNum').addClass("hidden");
    $('#limitNum').val("");



  });

});
