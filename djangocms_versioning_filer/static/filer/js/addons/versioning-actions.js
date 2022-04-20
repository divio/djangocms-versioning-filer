(function($) {

  if (!$) {
      return;
  }

  // Create burger menu:
  $(function() {
    let createBurgerMenu = function createBurgerMenu(row) {

        let actions = $(row).children('.column-action');
        if (!actions.length || !$(actions[0]).children('.action-button').length) {
          /* skip any rows without actions to avoid errors */
          return;
        }

        /* create burger menu anchor icon */
        let icon = document.createElement('span');
        icon.setAttribute('class', "fa fa-bars");

        let anchor = document.createElement('a');
        anchor.setAttribute('class', 'action-button cms-versioning-action-btn closed');
        anchor.setAttribute('title', 'Actions');
        anchor.appendChild(icon);

        /* create options container */
        let optionsContainer = document.createElement('div');
        let ul = document.createElement('ul');

        /* 'cms-actions-dropdown-menu' class is the main selector for the menu,
        'cms-actions-dropdown-menu-arrow-right-top' keeps the menu arrow in position. */
        optionsContainer.setAttribute(
          'class',
          'cms-actions-dropdown-menu cms-actions-dropdown-menu-arrow-right-top');
        ul.setAttribute('class', 'cms-actions-dropdown-menu-inner');

        /* get the existing actions and move them into the options container */
        $(actions[0]).children('.action-button').each(function (index, item) {

          let li = document.createElement('li');
          /* create an anchor from the item */
          let li_anchor = document.createElement('a');
          li_anchor.setAttribute('class', 'cms-actions-dropdown-menu-item-anchor');
          li_anchor.setAttribute('href', $(item).attr('href'));

          if ($(item).hasClass('cms-form-get-method')) {
            li_anchor.classList.add('cms-form-get-method'); // Ensure the fake-form selector is propagated to the new anchor
          }
          /* move the icon image */
          li_anchor.appendChild($(item).children('span')[0]);

          /* create the button text and construct the button */
          let span = document.createElement('span');
          span.appendChild(
            document.createTextNode(item.title)
          );

          li_anchor.appendChild(span);
          li.appendChild(li_anchor);
          ul.appendChild(li);

          /* destroy original replaced buttons */
          actions[0].removeChild(item);
        });

        /* add the options to the drop-down */
        optionsContainer.appendChild(ul);
        actions[0].appendChild(anchor);
        document.body.appendChild(optionsContainer);

        /* listen for burger menu clicks */
        anchor.addEventListener('click', function (ev) {
          ev.stopPropagation();
          toggleBurgerMenu(anchor, optionsContainer);
        });

        /* close burger menu if clicking outside */
        $(window).click(function () {
          closeBurgerMenu();
        });
      };

    let toggleBurgerMenu = function toggleBurgerMenu(burgerMenuAnchor, optionsContainer) {
      let bm = $(burgerMenuAnchor);
      let op = $(optionsContainer);
      let closed = bm.hasClass('closed');
      closeBurgerMenu();

      if (closed) {
        bm.removeClass('closed').addClass('open');
        op.removeClass('closed').addClass('open');
      } else {
        bm.addClass('closed').removeClass('open');
        op.addClass('closed').removeClass('open');
      }

      let pos = bm.offset();
      op.css('left', pos.left - 200);
      op.css('top', pos.top);
    };

    let closeBurgerMenu = function closeBurgerMenu() {
      $('.cms-actions-dropdown-menu').removeClass('open');
      $('.cms-actions-dropdown-menu').addClass('closed');
      $('.cms-versioning-action-btn').removeClass('open');
      $('.cms-versioning-action-btn').addClass('closed');
    };

    $('#result_list').find('tr').each(function (index, item) {
      createBurgerMenu(item);
    });

  });

})((typeof django !== 'undefined' && django.jQuery) || (typeof CMS !== 'undefined' && CMS.$) || false);