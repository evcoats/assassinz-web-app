from django import template
register = template.Library()

@register.simple_tag
def navbar_signedin():
    return  '''
    <nav class = "navbar navbar-expand-sm navbar-light">
      <div class = "container-fluid">
      <a class = "nabar-brand brand-text brandLink" href = "{% url 'index'%}"> <img class =  "nav-img" src = "{% static 'images/logoorgeyes.png' %}"> ASSASSIN <span class = "flame"> LIVE </span> </a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarTogglerDemo01" aria-controls="navbarTogglerDemo01" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
      <ul class="nav navbar-nav navbar-right">
        <div class="collapse navbar-collapse ">

        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle navRightLink" href="#" id="navbardrop" data-toggle="dropdown">
              <img src = "{% static 'images/play.png' %}" class = "icon">
          </a>
          <div class="dropdown-menu">
            <a class="dropdown-item" href="#">Your Games</a>
            <a class="dropdown-item" href="#">Join Game</a>
            <a class="dropdown-item" href="#">Start Game</a>
          </div>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle navRightLink" href="#" id="navbardrop" data-toggle="dropdown">  <img src = "{% static 'images/user.png' %}" class = "icon">
          </a>
          <div class="dropdown-menu dropdown-menu-right">
            <a class="dropdown-item" href="#">Profile</a>
            <a class="dropdown-item" href="#">Settings</a>
            <a class="dropdown-item" href="{% url 'signOut' %}">Sign Out</a>
          </div>
        </li>


      </div>

      </ul>
      </div>
    </nav>
      <div class="accordion-body collapse navbar-collapse" id = "navbarTogglerDemo01">

            <a class="dropdown-item" href="#">Your Games</a>
            <a class="dropdown-item" href="#">Join Game</a>
          <a class="dropdown-item" href="#">Start Game</a>
             <a class="dropdown-item" href="#">Profile</a>
            <a class="dropdown-item" href="#">Settings</a>
            <a class="dropdown-item" href="{% url 'signOut' %}">Sign Out</a>
          </div>
          <hr>
'''
