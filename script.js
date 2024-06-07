const buttons = document.querySelectorAll('.button');
const chatHistory = document.querySelector('.chat-container');
const messageInput = document.getElementById('user-input');
const sendButton = document.getElementById('send');
const chatWindow = document.querySelector('.chat-bar-container');
const formWindow = document.querySelector('.form-container');
const chatMessages = document.querySelector('.chat-messages');
const mainDownload = document.getElementById('download');
const mainShare = document.getElementById('share');
const progressBar = document.getElementById('progress');
const header = document.getElementById('header');
const nextButton = document.getElementById('next');
const submitButton = document.getElementById('submit');
const downloadButton = document.getElementById('downloadButton');
const downloadForm = document.getElementById('downloadForm');
const differentAddressCheckbox = document.getElementById('differentAddress');
const mailingAddressSection = document.getElementById('mailingAddress');
const monthlyPriceElements = document.querySelectorAll('.monthly-price');
const yearlyPriceElements = document.querySelectorAll('.yearly-price');
const yearlyPriceCrossedElements = document.querySelectorAll('.yearly-price-crossed');
const backendUrl = 'http://127.0.0.1:8000/';
// const backendUrl = 'https://justiguide.org/';
const tabLinks = document.querySelectorAll('.sidebar a');
const tabContents = document.querySelectorAll('.content .tab');
const emailInput = document.getElementById('emailInput');
const emailButton = document.getElementById('emailButton');
const googleButton = document.getElementById('googleButton');
const loginContainer = document.querySelector('.login-window');
const upgradeAlert = document.getElementById('upgrade_alert');
const alertTitle = document.getElementById('alert_title');
const alertContent = document.getElementById('alert_content');
const closeBtn = document.getElementById('close-btn');
const assistantBtn = document.querySelector('a[id="assistant"]');
const botOptions = document.querySelector('.botOptions');
const reloOpt = document.querySelector('.relo-selection');
const doloresOpt = document.querySelector('.dolores-selection');
const downloadFormContainer = document.querySelector('.downloadForm-container');

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    const cookieData = parts.pop().split(';').shift();
    const [username, firstName, lastName, email, user_location, profilePicUrl] = cookieData.split('|');
    return { username, firstName, lastName, email, user_location, profilePicUrl };
  }
  // else {
  //     const username = 'rajanpande';
  //     const firstName = 'Rajan';
  //     const lastName = 'Pande';
  //     const email = 'panderajan1996@gmail.com';
  //     const profilePicUrl = 'https://lh3.googleusercontent.com/a/ACg8ocLSpnnjCN1nbp0YmOax2v3KBzzedo_X9pxtXujLphgR_xqi9NuG7g=s288-c-no';
  //     return { username, firstName, lastName, email, profilePicUrl };
  // }
  return null;
}

function checkUser() {
  const email_id = emailInput.value;
  if (email_id) {
    fetch(`${backendUrl}check_user/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email_id })
    })
      .then(response => response.json())
      .then(data => {
        if (data.exists) {
          showLoginPasswordForm(email_id);
        } else {
          showRegistrationForm(email_id);
        }
      })
      .catch(error => console.error(error));
  } else {
    showRegistrationForm(email_id);
  }
}

function showLoginPasswordForm(email) {
  const passwordForm = `
        <div class="passForm">
            <div class="passDets">
                <input type="email" value="${email}" disabled>
                <input type="password" id="passwordInput" placeholder="Enter your password">
            </div>
            <div class="passButtons">
                <button id="backButton" class="passButton">Go Back</button>
                <button id="loginButton">Login</button>
            </div>
        </div>
    `;
  loginContainer.innerHTML = `
        <h2 id="passwordText">Login</h2>
        ${passwordForm}
    `;
  const passwordInput = document.getElementById('passwordInput');
  const backButton = document.getElementById('backButton');
  const loginButton = document.getElementById('loginButton');

  backButton.addEventListener('click', showEmailForm);
  loginButton.addEventListener('click', login);
}

function validatePassword(password, confirmPassword, passwordError, createAccountButton) {
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

  if (password !== confirmPassword) {
    passwordError.textContent = 'Passwords do not match';
    createAccountButton.disabled = true;
  } else if (!passwordRegex.test(password)) {
    passwordError.textContent = 'Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character';
    createAccountButton.disabled = true;
  } else {
    passwordError.textContent = '';
    createAccountButton.disabled = false;
  }
}

function showRegistrationForm(email) {
  const registrationForm = `
    <form id="registrationForm">
        <input type="email" id="regEmailInput" value="${email}" disabled>
        <div class="regName">
            <input type="text" id="firstNameInput" placeholder="First Name">
            <input type="text" id="lastNameInput" placeholder="Last Name">
        </div>
        <div class="regPass">
            <input type="password" id="regPasswordInput" placeholder="Enter your password">
            <input type="password" id="confirmPasswordInput" placeholder="Confirm your password">
        </div>
        <p id="passwordError" class="error"></p>
        <div class="regButtons">
            <button id="backButton">Go Back</button>
            <button type="button" id="createAccountButton" disabled>Create Account</button>
        </div>
    </form>
    <!--<div id="separator">
        <span>OR</span>
    </div>
    <button id="googleButton">
        <span class="icon"></span>
        <span class="buttonText">Sign in with Google</span>
    </button>-->
    `;
  loginContainer.innerHTML = `
        <h2 id="regText">Register</h2>
        ${registrationForm}
    `;
  const regEmailInput = document.getElementById('regEmailInput');
  const firstNameInput = document.getElementById('firstNameInput');
  const lastNameInput = document.getElementById('lastNameInput');
  const regPasswordInput = document.getElementById('regPasswordInput');
  const confirmPasswordInput = document.getElementById('confirmPasswordInput');
  const passwordError = document.getElementById('passwordError');
  const backButton = document.getElementById('backButton');
  const createAccountButton = document.getElementById('createAccountButton');

  backButton.addEventListener('click', showEmailForm);
  regPasswordInput.addEventListener('input', () => {
    validatePassword(regPasswordInput.value, confirmPasswordInput.value, passwordError, createAccountButton);
  });
  confirmPasswordInput.addEventListener('input', () => {
    validatePassword(regPasswordInput.value, confirmPasswordInput.value, passwordError, createAccountButton);
  });



  createAccountButton.addEventListener('click', showProfileForm);
}

function checkUsername(doneButton, username, usernameError) {
  fetch(`${backendUrl}check_username/`, {
    method: 'POST',
    body: JSON.stringify({ username })
  })
    .then(response => response.json())
    .then(data => {
      if (data.exists) {
        usernameError.textContent = 'Username already exists';
        doneButton.disabled = true;
      } else {
        usernameError.textContent = '';
        doneButton.disabled = false;
      }
    })
    .catch(error => console.error(error));
}

function updateProfilePic(profilePicInput, profilePicCanvas) {
  const file = profilePicInput.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function () {
      const img = new Image();
      img.onload = function () {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const size = Math.min(img.width, img.height);
        canvas.width = canvas.height = 175;
        ctx.save();
        ctx.beginPath();
        ctx.arc(87.5, 87.5, 87.5, 0, 2 * Math.PI);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(img, (img.width - size) / 2, (img.height - size) / 2, size, size, 0, 0, 175, 175);
        ctx.restore();
        const dataURL = canvas.toDataURL(file.type);
        profilePicCanvas.getContext('2d').clearRect(0, 0, 175, 175);
        profilePicCanvas.getContext('2d').drawImage(canvas, 0, 0);
      };
      img.src = reader.result;
    }
    reader.readAsDataURL(file);
  }
}


function showProfileForm() {
  const profilePicUrl = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png"
  const regEmailInput = document.getElementById('regEmailInput');
  const firstNameInput = document.getElementById('firstNameInput');
  const lastNameInput = document.getElementById('lastNameInput');
  const regPasswordInput = document.getElementById('regPasswordInput');
  const email = regEmailInput.value;
  const username = email.split('@')[0];
  const profileForm = `
        <div class="profileFormLogin">
            <div class="profilPicLogin">
                <input type="file" id="profilePicInput" accept="image/png, image/jpeg" style="display: none;">
                <label for="profilePicInput" style="cursor: pointer;">                
                    <canvas id="profilePicCanvas" width="175" height="175" style="background-image: url('${profilePicUrl}');"></canvas>
                </label>
                Click here to edit
            </div>
            <div class="userDetsLogin">
                <input type="text" id="usernameInput" value="${username}">
                <p id="usernameError" class="error"></p>
                <input type="text" id="locationInput" placeholder="Location (optional)">
            </div>
        </div>
        <button id="doneButton">Done</button>
    `;
  loginContainer.innerHTML = `
        <h2 id="profileText">Profile</h2>
        ${profileForm}
    `;
  const usernameInput = document.getElementById('usernameInput');
  const usernameError = document.getElementById('usernameError');
  const locationInput = document.getElementById('locationInput');
  const profilePicInput = document.getElementById('profilePicInput');
  const profilePicCanvas = document.getElementById('profilePicCanvas');
  const doneButton = document.getElementById('doneButton');
  let newProfilePic = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png"
  usernameInput.addEventListener('input', () => {
    checkUsername(doneButton, usernameInput.value, usernameError);
  });

  const formData = new FormData();
  profilePicInput.addEventListener('change', () => {
    updateProfilePic(profilePicInput, profilePicCanvas)
    const file = profilePicInput.files[0];
    formData.append('profilePic', file);
    formData.append('email_id', email);

  });
  doneButton.addEventListener('click', () => {
    registerUser(email, firstNameInput.value, lastNameInput.value, regPasswordInput.value, usernameInput.value, locationInput.value);
    fetch(`${backendUrl}uploadProfilePic/`, {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.resp) {
          newProfilePic = data.url;
        }
        else {

          console.log('Error uploading the pic: ', data.error)
        }
      })
      .catch(error => {
        console.error('Error uploading the pic: ', error);
      })
      .finally(() => {
        updateUserData(firstNameInput.value, lastNameInput.value, usernameInput.value, locationInput.value, newProfilePic, email);
        createLoginCookie(usernameInput.value, firstNameInput.value, lastNameInput.value, email, newProfilePic, locationInput.value);
        loginContainer.setAttribute('style', 'display: none;');
        showUserPage(usernameInput.value, firstNameInput.value, lastNameInput.value, email, newProfilePic, locationInput.value);
      });

  });


}

function registerUser(email, firstName, lastName, password, username, user_location = "", profilePic = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png") {
  const formData = { email, firstName, lastName, password, user_location, profilePic, username }
  fetch(`${backendUrl}register/`, {
    method: 'POST',
    body: JSON.stringify(formData)
  })
    .then(response => response.json())
    .then(data => {
      console.log('User Registered!');
    })
    .catch(error => console.error(error));
}


function showEmailForm() {
  loginContainer.innerHTML = `
        <h2 id="emailformText">Register/Login</h2>
        <div class="emailForm" id="emailForm">
            <input type="email" id="emailInput" placeholder="Enter your email">
            <button id="emailButton"></button>
        </div>
        <div id="separator">
            <span>OR</span>
        </div>
        <button id="googleButton">                    
            <span class="icon"></span>
            <span class="buttonText">Sign in with Google</span>
        </button>
    `;
}


function login() {
  const emailInput = document.querySelector('input[type="email"]');
  const passwordInput = document.getElementById('passwordInput');
  const email = emailInput.value;
  const password = passwordInput.value;
  fetch(`${backendUrl}check_login/`, {
    method: 'POST',
    body: JSON.stringify({
      'email': email,
      'password': password
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data['resp'] == true) {
        const { username, firstName, lastName, email, profilePicUrl, user_location } = data;
        console.log(email);
        createLoginCookie(username, firstName, lastName, email, profilePicUrl, user_location);
        document.getElementById("login-window").setAttribute("style", "display: none");
        showUserPage(username, firstName, lastName, email, profilePicUrl, user_location)

      }

    })
    .catch(error => console.error(error));
}

async function showUserPage(username, firstName, lastName, email, profilePicUrl, user_location) {
  const data = await getProfilePic(email);
  let newProfilePic;
  if (data.result) {
    newProfilePic = data.profilePic;
  } else {
    newProfilePic = profilePicUrl;
  }
  const profileContainer = document.getElementById('profile-container');
  profileContainer.removeAttribute('style');
  const tabLinks = document.querySelectorAll('.sidebar a');
  const tabContents = document.querySelectorAll('.content .tab');
  const userData = {
    profilePic: newProfilePic,
    username: username,
    firstName: firstName,
    lastName: lastName,
    user_location: user_location,
    email: email
  };
  tabLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const targetTab = e.target.getAttribute('data-tab');
      tabLinks.forEach(link => link.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      e.target.classList.add('active');
      const contentDiv = document.querySelector('.content');
      contentDiv.innerHTML = '';
      const newTabContent = document.createElement('div');
      newTabContent.id = targetTab;
      newTabContent.classList.add('tab', 'active');
      contentDiv.appendChild(newTabContent);
      loadTabContent(targetTab, userData);
    });
  });
  const chatButton = document.getElementById('chat');
  chatButton.removeAttribute('style');
  const formButton = document.getElementById('form');
  formButton.removeAttribute('style');
  loadTabContent('profile', userData);
  addUser(backendUrl, firstName, lastName, email, username, user_location, password = null, profilePic = profilePicUrl);


}

async function getSubscription() {
  const email_id = getCookie('username').email;
  try {
    const response = await fetch(`${backendUrl}user_sub/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email_id })
    });
    const data = await response.json();
    return data.subscription;
  } catch (error) {
    console.error('Error: ', error);
  }
}

function updateCurrentPlan(userPlan) {
  let lowercasePlan;
  if (typeof userPlan === 'string') {
    lowercasePlan = userPlan.toLowerCase();
  } else {
    lowercasePlan = String(userPlan).toLowerCase();
  }
  const planCards = document.querySelectorAll('.plan-card');
  if (planCards.length > 0) {
    for (let i = 0; i < planCards.length; i++) {
      planCards[i].classList.remove('current');
    }
    const buttons = [];
    for (let i = 0; i < planCards.length; i++) {
      const planCardButtons = planCards[i].querySelectorAll('.plan-button');
      for (let j = 0; j < planCardButtons.length; j++) {
        buttons.push(planCardButtons[j]);
      }
    }
    if (buttons.length > 0) {
      for (let i = 0; i < buttons.length; i++) {
        buttons[i].removeAttribute('id');
      }
      for (let i = 0; i < buttons.length; i++) {
        buttons[i].textContent = 'Start Free Trial';
      }
    }
    const currentPlanCard = document.getElementById(lowercasePlan);

    if (currentPlanCard) {
      currentPlanCard.classList.add('current');
      const currentPlanButton = currentPlanCard.querySelector('.plan-button');
      if (currentPlanButton) {
        currentPlanButton.id = 'current-plan';
        currentPlanButton.textContent = 'Current Plan';
      }
    }
  }
}

function showLoginWindow() {
  document.getElementById("login-window").style.display = "block";
  try {
    document.getElementById("profile-container").style.display = "none";
  } catch {

  }
  document.getElementById("download").style.display = "none";
  document.getElementById("share").style.display = "none";
}


function addUserMessage(message, profilePicUrl) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('user-message');
  messageElement.innerHTML = `
    <div class="user-profile">
      <svg class="user-avatar" id="userPic" style="background-image: url(${profilePicUrl})"></svg>
    </div>
    <div class="message-bubble">
      <p>${message}</p>
    </div>
  `;
  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(message) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('bot-message');
  messageElement.innerHTML = `
    <div class="bot-profile">
      <svg class="bot-avatar"></svg>
    </div>
    <div class="message-bubble">
      <p>${message}</p>
    </div>
  `;
  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addGeneratingMessage() {
  const messageElement = document.createElement('div');
  messageElement.classList.add('bot-message');
  messageElement.innerHTML = `
    <div class="bot-profile loading">
      <svg class="bot-avatar loading"></svg>
    </div>
    <div class="message-bubble loading">
      <svg class="ellipsis-gif"></svg>
    </div>
  `;
  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeGeneratingMessage() {
  const botProfileElement = document.querySelector('.bot-profile.loading');
  const botAvatarElement = document.querySelector('.bot-avatar.loading');
  if (botProfileElement) {
    botProfileElement.remove();
    botAvatarElement.remove();
  }
  const messageBubbleElement = document.querySelector('.message-bubble.loading');
  if (messageBubbleElement) {
    messageBubbleElement.remove();
  }
}

function signOut() {
  document.getElementById('signout-modal').style.display = 'block';
  document.getElementById('sides').style.zIndex = '0';
  document.cookie = "username=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
}

function closeSignOutModal() {
  document.getElementById('signout-modal').style.display = 'none';
}

function confirmSignOut() {
  document.getElementById("profile-container").setAttribute("style", "display: none;");
  closeSignOutModal();
  document.getElementById("login-window").setAttribute("style", "display: block;");
  startApp();
  document.getElementById("form").style.display = "none";
  location.reload();
}

function hideAll() {
  const formWindow = document.querySelector('.form-container');
  const chatWindow = document.querySelector('.chat-bar-container');
  const chatHistory = document.querySelector('.chat-container');
  downloadFormContainer.style.display = 'none';
  document.getElementById("disclaimer").setAttribute('style', 'display: none')
  if (chatWindow.classList.contains('active')) {
    chatWindow.classList.remove('active');
  }
  if (chatHistory.classList.contains('active')) {
    chatHistory.classList.remove('active');
  }
  if (formWindow.classList.contains('active')) {
    formWindow.classList.remove('active');
  }
  const mainDownload = document.getElementById('download');
  const mainShare = document.getElementById('share');
  mainDownload.setAttribute('style', 'display: none;');
  mainShare.setAttribute('style', 'display: none;');
  document.getElementById("login-window").setAttribute("style", "display: none");
  try {
    document.getElementById("profile-container").setAttribute("style", "display: none");
  }
  catch {

  }
  botOptions.setAttribute('style', 'display: none;')
  document.getElementById("subscription-container").setAttribute("style", "display: none");
}

function updatePlanPrices() {
  const selectedDuration = document.querySelector('input[name="plan-duration"]:checked').value;

  monthlyPriceElements.forEach((element) => {
    element.style.display = selectedDuration === 'monthly' ? 'inline' : 'none';
  });

  yearlyPriceElements.forEach((element) => {
    element.style.display = selectedDuration === 'yearly' ? 'inline' : 'none';
  });

  yearlyPriceCrossedElements.forEach((element) => {
    element.style.display = selectedDuration === 'yearly' ? 'inline' : 'none';
  });
}

async function subscription() {
  const userPlan = await getSubscription()
  updateCurrentPlan(userPlan)
  const planDurationRadios = document.querySelectorAll('input[name="plan-duration"]');
  document.getElementById("login-window").setAttribute("style", "display: none;");
  hideAll();
  try {
    document.getElementById("profile-container").setAttribute("style", "display: none");
  }
  catch {

  }
  document.getElementById("subscription-container").removeAttribute("style")
  updatePlanPrices();
  planDurationRadios.forEach((radio) => {
    radio.addEventListener('change', updatePlanPrices);
  });
}

async function getMessageNum() {
  const sub = await getSubscription();
  if (sub == 'free' || sub == 'Free') {
    const email_id = getCookie('username').email
    try {
      const response = await fetch(`${backendUrl}free_chatLimit/`, {
        method: 'POST',
        body: JSON.stringify({ email_id })
      });
      if (!response.ok) {
        console.error('HTTP error: ', response.status);
      }
      const data = await response.json();
      const retVal = {
        bool: data.result,
        num: data.num
      }
      return retVal;
    } catch (error) {
      console.error('Error: ', error);
    }
  } else {
    return null
  }
}

function handleRadioButtonChange(event, extraElements) {
  const selectedValue = event.target.value;
  extraElements.forEach(element => {
    element.style.display = 'none';
  });
  const elementsToShow = document.querySelectorAll(`.user-immiProc [id^="text-${selectedValue}"], .user-immiProc [for^="text-${selectedValue}"]`);
  elementsToShow.forEach(element => {
    element.style.display = 'block';
  });
}

async function setActiveButton(clickedButton) {
  const botIcon = document.querySelector('svg[id="assistant"]');
  buttons.forEach(button => button.classList.remove('active'));
  const parentClassList = clickedButton.parentElement.classList;
  var assistantID = 'relo';
  if (parentClassList.contains("side-container") || parentClassList.contains("menu-container") || parentClassList.contains("chat-bar-container")) {
    clickedButton.classList.add('active');
    if (clickedButton.id == 'chat') {
      hideAll();
      assistantBtn.addEventListener('click', function () {
        if (botOptions.style.display == 'none') {
          botOptions.style.display = 'block';
          botIcon.style.backgroundImage = 'url("https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/cross-button.png")';
          botIcon.style.opacity = 0.2;
        } else {
          botOptions.style.display = 'none';
          botIcon.style.backgroundImage = `url("https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/unnamed_${assistantID}.png")`;
          botIcon.style.opacity = 1;
        }
      })
      const sub = await getSubscription();
      if (sub != 'Free' && sub != 'Basic') {
        assistantBtn.removeAttribute('style');
      }
      if (!chatWindow.classList.contains('active')) {
        chatWindow.classList.add('active');
      }
      if (!chatHistory.classList.contains('active')) {
        chatHistory.classList.add('active');
      }
      const toBlock = await getMessageNum();
      if (toBlock) {
        if (toBlock.bool) {
          alertTitle.textContent = 'Upgrade your Subscription!';
          alertContent.textContent = 'You have reached the limit of free messages. To continue using the chat without any restrictions, please upgrade to the "Basic" tier.';
          sendButton.style.pointerEvents = 'none';
          sendButton.style.cursor = 'not-allowed';
          messageInput.disabled = true;
        } else {
          alertTitle.textContent = 'Upgrade your Subscription!';
          alertContent.textContent = `You have ${4 - parseInt(toBlock.num)} messages left. To enjoy unlimited access to the chat, consider upgrading to the "Basic" tier.`;
        }
        upgradeAlert.style.display = 'block';
        closeBtn.addEventListener('click', () => {
          upgradeAlert.style.display = 'none';
        });
      }
      botIcon.style.backgroundImage = 'url("https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/unnamed_relo.png")';
      const iconLoc = 'https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/unnamed_';
      botIcon.style.backgroundImage = `url('${iconLoc}${assistantID}.png')`;
      reloOpt.addEventListener('click', function () {
        assistantID = reloOpt.classList[0].split('-selection')[0];
        botOptions.setAttribute('style', 'display: none;');
        botIcon.style.backgroundImage = 'url("https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/unnamed_relo.png")';
        botIcon.style.opacity = 1;
      })
      doloresOpt.addEventListener('click', function () {
        assistantID = doloresOpt.classList[0].split('-selection')[0];
        botOptions.setAttribute('style', 'display: none;');
        botIcon.style.backgroundImage = 'url("https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/chat/unnamed_dolores.png")'
        botIcon.style.opacity = 1;
      })
      document.getElementById("disclaimer").removeAttribute('style');
      messageInput.addEventListener('keyup', () => {
        const message = messageInput.value.trim();
        if (message) {
          sendButton.addEventListener('click', async (event) => {
            event.preventDefault();
            if (messageInput.value != '') {
              addUserMessage(messageInput.value, getCookie('username').profilePicUrl);
              const messageVal = messageInput.value;
              addGeneratingMessage();
              fetch(`${backendUrl}get_response/`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  user_message: messageVal,
                  user: getCookie('username').username,
                  assistant: assistantID
                })
              })
                .then(response => response.json())
                .then(data => {
                  const botResponse = data.bot_response;
                  removeGeneratingMessage();
                  addBotMessage(botResponse);
                })
                .catch((error) => {
                  console.error('Error: ', error);
                });
              messageInput.value = '';
              const toBlock = await getMessageNum();
              if (toBlock) {
                if (toBlock.bool) {
                  alertTitle.textContent = 'Upgrade your Subscription!';
                  alertContent.textContent = 'You have reached the limit of free messages. To continue using the chat without any restrictions, please upgrade to the "Basic" tier.';
                  sendButton.style.pointerEvents = 'none';
                  sendButton.style.cursor = 'not-allowed';
                  messageInput.disabled = true;
                } else {
                  alertTitle.textContent = 'Upgrade your Subscription!';
                  alertContent.textContent = `You have ${4 - parseInt(toBlock.num)} messages left. To enjoy unlimited access to the chat, consider upgrading to the "Basic" tier.`;
                }
                upgradeAlert.style.display = 'block';
                closeBtn.addEventListener('click', () => {
                  upgradeAlert.style.display = 'none';
                });
              }
            }
          });
          messageInput.addEventListener('keydown', async (event) => {
            if (event.key === 'Enter') {
              if (messageInput.value != '') {
                addUserMessage(messageInput.value, getCookie('username').profilePicUrl);
                const messageVal = messageInput.value;
                addGeneratingMessage();
                fetch(`${backendUrl}get_response/`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    user_message: messageVal,
                    user: getCookie('username').username,
                    assistant: assistantID
                  })
                })
                  .then(response => response.json())
                  .then(data => {
                    const botResponse = data.bot_response;
                    removeGeneratingMessage();
                    addBotMessage(botResponse);
                  })
                  .catch((error) => {
                    console.error('Error: ', error);
                  });
                messageInput.value = '';
                const toBlock = await getMessageNum();
                if (toBlock) {
                  if (toBlock.bool) {
                    alertTitle.textContent = 'Upgrade your Subscription!';
                    alertContent.textContent = 'You have reached the limit of free messages. To continue using the chat without any restrictions, please upgrade to the "Basic" tier.';
                    sendButton.style.pointerEvents = 'none';
                    sendButton.style.cursor = 'not-allowed';
                    messageInput.disabled = true;
                  } else {
                    alertTitle.textContent = 'Upgrade your Subscription!';
                    alertContent.textContent = `You have ${4 - parseInt(toBlock.num)} messages left. To enjoy unlimited access to the chat, consider upgrading to the "Basic" tier.`;
                  }
                  upgradeAlert.style.display = 'block';
                  closeBtn.addEventListener('click', () => {
                    upgradeAlert.style.display = 'none';
                  });
                }
              }
            }
          });
        }
      });
    } else if (clickedButton.id == 'form') {
      hideAll();
      if (!formWindow.classList.contains('active')) {
        formWindow.classList.add('active');
      }
      formWindow.removeAttribute('style');
      const DsignInput = document.getElementById("part-d-applicant");
      const DsignTitle = DsignInput.querySelector('.sign-title');
      const DsignSubtitle = DsignInput.querySelector('.sign-subtitle');
      const DsignSelected = DsignInput.querySelector('.sign-uploaded');
      const DhiddenFileInput = DsignInput.querySelector("#hiddenFileInput");

      const formParts = document.querySelector('.parts');
      const formMenu = document.getElementById('form-parts');
      var partSelectionElements = document.querySelectorAll('.part-selection');
      const sectionHeader = document.querySelector('.section-header');
      const sectionSubhead = document.querySelector('.section-subhead');
      const allSections = document.querySelectorAll('.section, .section-end');
      const sectionEndElements = document.querySelectorAll('.section-end button');
      const sectionOrder = ['part-a-i', 'part-a-ii', 'part-a-iii', 'part-b', 'part-c', 'part-d', 'part-suppAB'];
      const diffMailAddCheckbox = document.getElementById("diffMailAdd");
      const diffMailAddContainer = document.getElementById("diffMailAdd-container");

      function openFormMenu() {        
        const getActivePart = formParts.querySelector('#active a[id="part-selection"]').className;
        if (formParts.style.display == 'flex') {
          formParts.style.display = 'none';
          formMenu.style.opacity = 0.5;
        } else {
          formParts.style.display = 'flex';
          formMenu.style.opacity = 1;
        }
      }

      function toggleMailingAddress() {
        if (diffMailAddCheckbox.checked) {
          diffMailAddContainer.style.removeProperty('display')
        } else {
          diffMailAddContainer.style.display = "none";
        }
      }


      diffMailAddCheckbox.addEventListener('change', toggleMailingAddress);
      toggleMailingAddress();

      function handlePartSelection(event) {
        const clickedElement = event.currentTarget;
        const currentSectionId = clickedElement.children[0].className
        const currentIndex = sectionOrder.indexOf(currentSectionId);
        const previousIndex = (currentIndex + 1) % sectionOrder.length;
        var prevSectionId = null;
        var unfilledValues = null;
        if (previousIndex !== -1) {
          prevSectionId = sectionOrder[previousIndex]
          unfilledValues = getUnfilledList(prevSectionId)
        }
        partSelectionElements.forEach(element => {
          element.removeAttribute('id');
        });
        clickedElement.id = 'active';
        const childAnchorClass = clickedElement.querySelector('a').className;
        if (sectionHeader) {
          for (const child of sectionHeader.children) {
            if (child.tagName === 'A' && child.id === childAnchorClass) {
              child.style.removeProperty('display');
            } else {
              child.style.display = 'none';
            }
          }
        }
        if (sectionSubhead) {
          for (const child of sectionSubhead.children) {
            if (child.tagName === 'P' && child.id === childAnchorClass) {
              child.style.removeProperty('display');
            } else {
              child.style.display = 'none';
            }
          }
        }
        allSections.forEach(section => {
          if (section.id === childAnchorClass) {
            section.style.display = 'flex';
          } else {
            section.style.display = 'none';
          }
        });
        const scrollableContent = document.querySelector('.scrollable-content');
        if (scrollableContent) {
          scrollableContent.scrollTop = 0;
        }


      }

      function getUnfilledList(currentSectionId) {
        const requiredElements = Array.from(document.querySelectorAll(`#${currentSectionId}.section .required`))
        const unfilledValues = []
        for (var ind in requiredElements) {
          if (currentSectionId != 'part-suppAB') {
            if (requiredElements[ind].type == 'text' || requiredElements[ind].type == 'date') {
              if (requiredElements[ind].value === '') {
                unfilledValues.push(requiredElements[ind])
              }
            } else if (requiredElements[ind].tagName == 'DIV') {
              if (requiredElements[ind].className.includes('radio-group')) {
                const inputRadio = requiredElements[ind].querySelector(`.radio-set input`).name;
                const isAnyRadioUnchecked = document.querySelector(`input[name="${inputRadio}"]:checked`) === null;
                if (isAnyRadioUnchecked) {
                  unfilledValues.push(requiredElements[ind])
                }
              } else if (requiredElements[ind].className.includes('checkbox-group')) {
                const inputCheckbox = requiredElements[ind].querySelector(`.checkbox-set input`).id;
                const isAnyCheckboxUnchecked = document.querySelector(`input[id="${inputCheckbox}"]:checked`) === null;
                if (isAnyCheckboxUnchecked) {
                  unfilledValues.push(requiredElements[ind])
                }
              } else if (requiredElements[ind].className.includes('sign-input')) {
                const nosignFile = requiredElements[ind].querySelector('input[type="file"]').files.length === 0;
                if (nosignFile) {
                  unfilledValues.push(requiredElements[ind])
                }
              }
            }
          } else {
            const selectElement = document.querySelector(`#${currentSectionId}.section select[name="part"]`);
            const selectedValue = selectElement.value;
            if (selectedValue !== 'start') {
              if (requiredElements[ind].value === '') {
                unfilledValues.push(requiredElements[ind])
              }
            }
          }
        }
        return unfilledValues;

      }
      const formDataDictionary = {};
      const allUnfilled = [];
      function handleSectionEndClick(event) {
        const currentSectionId = event.currentTarget.parentElement.id;
        const unfilledValues = getUnfilledList(currentSectionId)
        if (unfilledValues.length === 0) {
          const inputElements = document.querySelectorAll(`#${currentSectionId}.section input`);
          inputElements.forEach((input) => {
            const { type, id, value, checked, files } = input;
            if (type === 'text') {
              formDataDictionary[`${currentSectionId}-${id}`] = value;
            } else if (type === 'date') {
              if (value !== '') {
                splitDates = value.split('-');
                if (id.includes('from') || id.includes('to')) {
                  formDataDictionary[`${currentSectionId}-${id}`] = `${splitDates[1]}/${splitDates[0]}`;
                } else {
                  formDataDictionary[`${currentSectionId}-${id}`] = `${splitDates[1]}/${splitDates[2]}/${splitDates[0]}`
                }
              } else {
                formDataDictionary[`${currentSectionId}-${id}`] = value
              }
            } else if (type === 'radio') {
              if (checked) {
                formDataDictionary[`${currentSectionId}-${id}`] = value;
              }
            } else if (type === 'checkbox') {
              if (!formDataDictionary[`${currentSectionId}-${id}`]) {
                formDataDictionary[`${currentSectionId}-${id}`] = [];
              }
              if (checked) {
                formDataDictionary[`${currentSectionId}-${id}`].push(value);
              }
              else if (id.includes('childrenCheck')) {
                formDataDictionary[`${currentSectionId}-${id}`] = ['yes']
              }
            } else if (type === 'file') {
              formDataDictionary[`${currentSectionId}-${id}`] = files[0]
            }
          });
          const textareaElements = document.querySelectorAll(`#${currentSectionId}.section textarea`);
          textareaElements.forEach((textarea) => {
            const { id, value } = textarea;
            formDataDictionary[`${currentSectionId}-${id}`] = value;
          })
          const selectElements = document.querySelectorAll(`#${currentSectionId}.section select`);
          selectElements.forEach((select) => {
            const { id, value } = select;
            const selectedOption = Array.from(select.options).find(option => option.value === value);
            const selectedOptionText = selectedOption ? selectedOption.textContent : '';
            formDataDictionary[`${currentSectionId}-${id}`] = selectedOptionText;
          })

          const currentIndex = sectionOrder.indexOf(currentSectionId);
          const nextIndex = (currentIndex + 1) % sectionOrder.length;
          const nextSectionId = sectionOrder[nextIndex];
          const nextPartSelection = document.querySelector(`.part-selection a[class="${nextSectionId}"]`);
          if (nextPartSelection) {
            nextPartSelection.click();
          }
          const scrollableContent = document.querySelector('.scrollable-content');
          if (scrollableContent) {
            scrollableContent.scrollTop = 0;
          }
          allUnfilled.push(currentSectionId);
        } else {
          const firstElement = unfilledValues[0].parentElement;
          firstElement.scrollIntoView({ behavior: 'smooth' });
        }
      }

      function findMissingVals(filled, master) {
        const missing = [];
        for (const value of master) {
          if (!filled.includes(value)) {
            missing.push(value);
          }
        }
        return missing;
      }

      sectionEndElements.forEach(element => {
        element.addEventListener('click', handleSectionEndClick);
      });
      const submitButton = document.getElementById('send-formButton');


      if (submitButton) {

        const email_id = getCookie('username').email;
        const preSubmit = sectionOrder.slice(0, -1);
        submitButton.addEventListener('click', async (event) => {
          const UnfilledIds = findMissingVals(allUnfilled, preSubmit);
          const thisId = 'part-suppAB'
          const unFilledVals = getUnfilledList(thisId);
          if (unFilledVals.length === 0 && UnfilledIds.length === 0) {
            currId = event.target.parentElement.id
            if (currId) {
              const inputElements = document.querySelectorAll(`#${currId}.section input`);
              inputElements.forEach((input) => {
                const { type, id, value, checked, files } = input;
                if (type === 'text') {
                  formDataDictionary[`${currId}-${id}`] = value;
                } else if (type === 'date') {
                  if (value !== '') {
                    splitDates = value.split('-');
                    if (id.includes('from') || id.includes('to')) {
                      formDataDictionary[`${currId}-${id}`] = `${splitDates[1]}/${splitDates[0]}`;
                    } else {
                      formDataDictionary[`${currId}-${id}`] = `${splitDates[1]}/${splitDates[2]}/${splitDates[0]}`
                    }
                  } else {
                    formDataDictionary[`${currId}-${id}`] = value
                  }
                } else if (type === 'radio') {
                  if (checked) {
                    formDataDictionary[`${currId}-${id}`] = value;
                  }
                } else if (type === 'checkbox') {
                  if (!formDataDictionary[`${currId}-${id}`]) {
                    formDataDictionary[`${currId}-${id}`] = [];
                  }
                  if (checked) {
                    formDataDictionary[`${currId}-${id}`].push(value);
                  }
                } else if (type === 'file') {
                  formDataDictionary[`${currId}-${id}`] = files[0]
                }
              });
              const textareaElements = document.querySelectorAll(`#${currId}.section textarea`);
              textareaElements.forEach((textarea) => {
                const { id, value } = textarea;
                formDataDictionary[`${currId}-${id}`] = value;
              })
              const selectElements = document.querySelectorAll(`#${currId}.section select`);
              selectElements.forEach((select) => {
                const { id, value } = select;
                const selectedOption = Array.from(select.options).find(option => option.value === value);
                const selectedOptionText = selectedOption ? selectedOption.textContent : '';
                formDataDictionary[`${currId}-${id}`] = selectedOptionText;
              })
            }
            formWindow.style.display = 'none';
            downloadFormContainer.removeAttribute('style');
            try {
              const formData = new FormData();
              formData.append('email_id', email_id);
              const textData = {};
              const listData = {};
              for (const sectionId in formDataDictionary) {
                const value = formDataDictionary[sectionId];
                if (sectionId.includes('hidden')) {
                  const keyList = sectionId.split('-')
                  const Input = document.getElementById(`${keyList[0]}-${keyList[1]}-applicant`)
                  const Inputfiles = Input.querySelector("#hiddenFileInput");
                  const newKey = sectionId.replaceAll("-", "");
                  const signImg = Inputfiles.files[0]
                  formData.append(newKey, signImg);

                } else if (Array.isArray(value) && value.length == 1) {
                  if (value[0] != '') {
                    textData[sectionId] = value[0];
                  }
                } else if (Array.isArray(value) && value.length > 1) {
                  listData[sectionId] = value;

                } else if (value != '') {
                  textData[sectionId] = value;
                }
              }
              formData.append('texts', JSON.stringify(textData));
              formData.append('lists', JSON.stringify(listData));
              const downloadFormText = document.getElementById('downloadForm-title')
              const downloadForm_Button = document.querySelector(".downloadButton-button #downloadForm")

              const response = await fetch(`${backendUrl}get_formData/`, {
                method: 'POST',
                body: formData
              });
              if (response.ok) {
                const responseData = await response.json();
                downloadFormText.textContent = 'Form Created Successfully!'
                downloadForm_Button.style.cursor = 'pointer';
                downloadForm_Button.style.opacity = 1;
                downloadForm_Button.onclick = function () {
                  location.href = responseData.uploaded;
                }
              } else {
                console.error(`HTTP error! Status: ${response.status}`)
              }
            } catch (error) {
              console.error('Error submitting form: ', error)
            }

          } else {
            if (UnfilledIds.length !== 0) {
              const nextPartSelection = document.querySelector(`.part-selection a[class="${UnfilledIds[0]}"]`);
              if (nextPartSelection) {
                nextPartSelection.click();
              }
              const scrollableContent = document.querySelector('.scrollable-content');
              if (scrollableContent) {
                scrollableContent.scrollTop = 0;
              }
            } else {
              const suppAB_firstElement = unFilledVals[0].parentElement;
              suppAB_firstElement.scrollIntoView({ behavior: 'smooth' });
            }
          }
        });
      }

      partSelectionElements.forEach(element => {
        element.addEventListener('click', handlePartSelection);
      });



      formMenu.addEventListener('click', openFormMenu);
      const addSuppABRespButton = document.getElementById("suppAB-resp");

      let suppABCounter = 0;

      addSuppABRespButton.addEventListener('click', () => {
        suppABCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const suppABAdditionalDiv = document.createElement('div');
        suppABAdditionalDiv.classList.add('suppAB-additional');
        suppABAdditionalDiv.id = `suppAB-additional-${suppABCounter}`;
        suppABAdditionalDiv.innerHTML = `
                <div class="divided-text" id="one-three">
                <div class="dropdown-input" id="full-width">
                    <label for="suppAB-part-${suppABCounter}" id="drop-box">Part</label>
                    <select id="suppAB-part-${suppABCounter}" class="dropbox" name="part">
                    <option value="start"></option>
                    <option value="part-a-i">Part A.I.</option>
                    <option value="part-a-ii">Part A.II.</option>
                    <option value="part-a-iii">Part A.III.</option>
                    <option value="part-b">Part B</option>
                    <option value="part-c">Part C</option>
                    <option value="part-d">Part D</option>
                    </select>
                </div>
                <div class="dropdown-input" id="full-width">
                    <label for="suppAB-ques-${suppABCounter}" id="drop-box">Question</label>
                    <select id="suppAB-ques-${suppABCounter}" class="dropbox" name="question">
                    <option value="start"></option>
                    <option value="part-a-i-mainInfo">Main Information</option>
                    <option value="part-a-i-residence">Residence</option>
                    <option value="part-a-i-mailAdd">Mailing Address</option>
                    <option value="part-a-i-genInfo">General Information</option>
                    <option value="part-a-i-usEntries">U.S. Entries</option>
                    <option value="part-a-i-passportInfo">Passport Information</option>
                    <option value="part-a-i-lang">Language</option>
                    <option value="part-a-ii-spouse">Spouse</option>
                    <option value="part-a-ii-children">Children</option>
                    <option value="part-a-iii-prevAdd">Addresses before coming to US</option>
                    <option value="part-a-iii-prevRes">Residences</option>
                    <option value="part-a-iii-edu">Education</option>
                    <option value="part-a-iii-employment">Employment</option>
                    <option value="part-a-iii-mother">Mother</option>
                    <option value="part-a-iii-father">Father</option>
                    <option value="part-a-iii-siblings">Siblings</option>
                    <option value="part-b-reason">Reason for asylum</option>
                    <option value="part-b-harm">Experience of harn or mistreatment</option>
                    <option value="part-b-fear">Fear of harm or mistreatment</option>
                    <option value="part-b-crime">Criminal activity</option>
                    <option value="part-b-orgAss">Organizational Association</option>
                    <option value="part-c-prevAppl">Previous applications</option>
                    <option value="part-c-prevLoc">Previous asylum claims</option>
                    <option value="part-c-causedHarm">Responsibility for Harm</option>
                    <option value="part-c-retCountry">Return to previous countries</option>
                    <option value="part-c-oneYear">Application after 1 year of last arrival
                    </option>
                    <option value="part-c-UScrimes">Criminal activity in the US</option>
                    <option value="part-d-assistFam">Assistance by family</option>
                    </select>
                </div>
                </div>
                <textarea rows="25" id="suppAB-resp-${suppABCounter}" class="textarea"></textarea>
                `;
        const suppABContainer = addSuppABRespButton.parentNode;
        suppABContainer.insertBefore(separatorDiv, addSuppABRespButton);
        suppABContainer.insertBefore(suppABAdditionalDiv, addSuppABRespButton);
        const partDropdowns = document.querySelectorAll('.suppAB-additional #one-three.divided-text .dropdown-input select[name="part"]');
        partDropdowns.forEach(dropdown => {
          dropdown.addEventListener('change', handlePartChange);
          handlePartChange({ target: dropdown });
        });
      });
      const partDropdowns = document.querySelectorAll('.suppAB-additional #one-three.divided-text .dropdown-input select[name="part"]');
      partDropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', handlePartChange);
        handlePartChange({ target: dropdown });
      });

      const addUSEntriesButton = document.getElementById("add-USentries");
      let usEntryCounter = 0;
      addUSEntriesButton.addEventListener('click', () => {
        usEntryCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const entryDiv = document.createElement('div');
        entryDiv.classList.add('additional-entries');
        entryDiv.id = `additional-entry-${usEntryCounter}`;
        entryDiv.innerHTML = `
                <div class="text-input" id="full-width">
                <label for="a-i-date-${usEntryCounter}" id="text-box">Date</label>
                <input type="date" id="a-i-date-${usEntryCounter}" class="textbox">
                </div>
                <div class="text-input" id="full-width">
                <label for="a-i-place-${usEntryCounter}" id="text-box">Place</label>
                <input type="text" id="a-i-place-${usEntryCounter}" class="textbox">
                </div>
                <div class="text-input" id="full-width">
                <label for="a-i-status-${usEntryCounter}" id="text-box">Status</label>
                <input type="text" id="a-i-status-${usEntryCounter}" class="textbox">
                </div>
                `;
        const entriesContainer = addUSEntriesButton.parentNode;
        entriesContainer.insertBefore(separatorDiv, addUSEntriesButton);
        entriesContainer.insertBefore(entryDiv, addUSEntriesButton);
      });

      const addPrevAddressesButton = document.getElementById("prevAddressesButton");
      const prevAddressesContainer = document.getElementById('address-0');
      let addressCounter = 0;
      addPrevAddressesButton.addEventListener('click', () => {
        addressCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const addressDiv = document.createElement('div');
        addressDiv.classList.add('address');
        addressDiv.id = `address-${addressCounter}`;
        addressDiv.innerHTML = `
                <div class="divided-text" id="three-three-three">
                <div class="text-input" id="full-width">
                    <label for="a-iii-address-${addressCounter}-country" id="text-box" class="required">Country</label>
                    <input type="text" id="a-iii-address-${addressCounter}-country" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-address-${addressCounter}-state" id="text-box" class="required">Department, Province or State</label>
                    <input type="text" id="a-iii-address-${addressCounter}-state" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-address-${addressCounter}-city" id="text-box" class="required">City/Town</label>
                    <input type="text" id="a-iii-address-${addressCounter}-city" class="textbox required">
                </div>
                </div>
                <div class="text-input" id="full-width">
                <label for="a-iii-address-${addressCounter}-street" id="text-box">Number and Street (provide if any)</label>
                <input type="text" id="a-iii-address-${addressCounter}-street" class="textbox">
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-address-${addressCounter}-date-from" id="text-box" class="required">Dates From</label>
                    <input type="date" id="a-iii-address-${addressCounter}-date-from" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-address-${addressCounter}-date-to" id="text-box" class="required">Dates To</label>
                    <input type="date" id="a-iii-address-${addressCounter}-date-to" class="textbox required">
                </div>
                </div>
                `;
        const addEntriesDiv = addPrevAddressesButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addPrevAddressesButton);
        addEntriesDiv.insertBefore(addressDiv, addPrevAddressesButton);
      });

      const addPrevResidencesButton = document.getElementById("prevRes");
      const prevResidencesContainer = document.getElementById('residence-0');
      let residenceCounter = 0;
      addPrevResidencesButton.addEventListener('click', () => {
        residenceCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const residenceDiv = document.createElement('div');
        residenceDiv.classList.add('residence');
        residenceDiv.id = `residence-${residenceCounter}`;
        residenceDiv.innerHTML = `
                <div class="divided-text" id="three-three-three">
                <div class="text-input" id="full-width">
                    <label for="a-iii-residence-${residenceCounter}-country" id="text-box" class="required">Country</label>
                    <input type="text" id="a-iii-residence-${residenceCounter}-country" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-residence-${residenceCounter}-state" id="text-box" class="required">Department, Province or State</label>
                    <input type="text" id="a-iii-residence-${residenceCounter}-state" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-residence-${residenceCounter}-city" id="text-box" class="required">City/Town</label>
                    <input type="text" id="a-iii-residence-${residenceCounter}-city" class="textbox required">
                </div>
                </div>
                <div class="text-input" id="full-width">
                <label for="a-iii-residence-${residenceCounter}-street" id="text-box" class="required">Number and Street</label>
                <input type="text" id="a-iii-residence-${residenceCounter}-street" class="textbox required">
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-residence-${residenceCounter}-date-from" id="text-box" class="required">Dates From</label>
                    <input type="date" id="a-iii-residence-${residenceCounter}-date-from" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-residence-${residenceCounter}-date-to" id="text-box" class="required">Dates To</label>
                    <input type="date" id="a-iii-residence-${residenceCounter}-date-to" class="textbox required">
                </div>
                </div>
                `;
        const addEntriesDiv = addPrevResidencesButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addPrevResidencesButton);
        addEntriesDiv.insertBefore(residenceDiv, addPrevResidencesButton);
      });

      const addEduHistoryButton = document.getElementById("eduHistory");
      const eduHistoryContainer = document.getElementById('education-0');

      let eduCounter = 0;

      addEduHistoryButton.addEventListener('click', () => {
        eduCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const educationDiv = document.createElement('div');
        educationDiv.classList.add('education');
        educationDiv.id = `education-${eduCounter}`;
        educationDiv.innerHTML = `
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-education-${eduCounter}-name" id="text-box" class="required">Name of School</label> <input type="text"
                    id="a-iii-education-${eduCounter}-name" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-education-${eduCounter}-type" id="text-box" class="required">Type of School</label> <input type="text"
                    id="a-iii-education-${eduCounter}-type" class="textbox required">
                </div>
                </div>
                <div class="text-input" id="full-width">
                <label for="a-iii-education-${eduCounter}-loc" id="text-box" class="required">Location (Address)</label> <input type="text"
                    id="a-iii-education-${eduCounter}-loc" class="textbox required">
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-education-${eduCounter}-dates-from" id="text-box" class="required">Dates From</label>
                    <input type="date"
                    id="a-iii-education-${eduCounter}-dates-from" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-education-${eduCounter}-dates-to" id="text-box" class="required">Dates To</label>
                    <input type="date"
                    id="a-iii-education-${eduCounter}-dates-to" class="textbox required">
                </div>
                </div>
                `;
        const addEntriesDiv = addEduHistoryButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addEduHistoryButton);
        addEntriesDiv.insertBefore(educationDiv, addEduHistoryButton);
      });
      const addEmplHistoryButton = document.getElementById("emplHistory");
      const emplHistoryContainer = document.getElementById('employment-0');

      let emplCounter = 0;

      addEmplHistoryButton.addEventListener('click', () => {
        emplCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const employmentDiv = document.createElement('div');
        employmentDiv.classList.add('employment');
        employmentDiv.id = `employment-${emplCounter}`;
        employmentDiv.innerHTML = `
                <div class="text-input" id="full-width">
                <label for="a-iii-employment-${emplCounter}-occ" id="text-box" class="required">Your Occupation</label> <input type="text"
                    id="a-iii-employment-${emplCounter}-occ" class="textbox required">
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-employment-${emplCounter}-name" id="text-box" class="required">Name of Employer</label> <input type="text"
                    id="a-iii-employment-${emplCounter}-name" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-employment-${emplCounter}-address" id="text-box" class="required">Address of Employer</label> <input type="text"
                    id="a-iii-employment-${emplCounter}-address" class="textbox required">
                </div>
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-employment-${emplCounter}-dates-from" id="text-box" class="required">Dates From</label>
                    <input type="date"
                    id="a-iii-employment-${emplCounter}-dates-from" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-employment-${emplCounter}-dates-to" id="text-box" class="required">Dates To</label>
                    <input type="date"
                    id="a-iii-employment-${emplCounter}-dates-to" class="textbox required">
                </div>
                </div>
                `;
        const addEntriesDiv = addEmplHistoryButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addEmplHistoryButton);
        addEntriesDiv.insertBefore(employmentDiv, addEmplHistoryButton);
      });
      const addSiblingsButton = document.getElementById("siblings");
      const siblingsContainer = document.getElementById('sibling-0');
      let siblingCounter = 0;

      addSiblingsButton.addEventListener('click', () => {
        siblingCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const siblingDiv = document.createElement('div');
        siblingDiv.classList.add('sibling');
        siblingDiv.id = `sibling-${siblingCounter}`;
        siblingDiv.innerHTML = `
                <div class="subsection-description">
                <a class="subsection-header" id="sibling-${siblingCounter}-header">Sibling</a>
                </div>
                <div class="toggle" id="sibling-${siblingCounter}-dec">
                <label class="switch-toggle">
                    <input type="checkbox" id="sibling-${siblingCounter}-dec" value="yes">
                    <span class="slider-toggle"></span>
                </label>
                <label id="toggle-label">Deceased</label>
                </div>
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="a-iii-sibling-${siblingCounter}-name" id="text-box" class="required">Full Name</label> <input type="text"
                    id="a-iii-sibling-${siblingCounter}-name" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="a-iii-sibling-${siblingCounter}-ccob" id="text-box" class="required">City/Town and Country of Birth</label>
                    <input type="text" id="a-iii-sibling-${siblingCounter}-ccob" class="textbox required">
                </div>
                </div>
                <div class="a-iii-sibling-${siblingCounter}-loc">
                  <div class="text-input" id="full-width">
                  <label for="a-iii-sibling-${siblingCounter}-loc" id="text-box">Current Location</label>
                  <input type="text" id="a-iii-sibling-${siblingCounter}-loc" class="textbox">
                  </div>
                </div>
                `;
        const addEntriesDiv = addSiblingsButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addSiblingsButton);
        addEntriesDiv.insertBefore(siblingDiv, addSiblingsButton);
      });

      const partBRadioButtons = document.querySelectorAll(
        'input[name="orgTorture"], input[name="orgPart"], input[name="orgAss"], input[name="crime"], input[name="fear"], input[name="harm"]'
      );
      const responseDivs_B = document.querySelectorAll(
        '.harm-responses, .orgTorture-responses, .orgPart-responses, .orgAss-responses, .crime-responses, .fear-responses'
      );
      function handlePartBRadioChange() {
        responseDivs_B.forEach(div => {
          div.style.display = 'none';
        });
        partBRadioButtons.forEach(radio => {
          if (radio.checked && radio.value === 'yes') {
            const responseDivId = `.${radio.name}-responses`;
            const responseDiv = document.querySelector(responseDivId);
            if (responseDiv) {
              responseDiv.style.display = 'block';
            }
          }
        });
      }
      partBRadioButtons.forEach(radio => {
        radio.addEventListener('change', handlePartBRadioChange);
      });
      handlePartBRadioChange();
      const partCRadioButtons = document.querySelectorAll(
        'input[name="crimeCommCheck"], input[name="oneYearCheck"], input[name="leftCountryCheck"],' +
        'input[name="causedHarmCheck"], input[name="lawfulStatus"], input[name="inCountry"], input[name="prevApplCheck"]'
      );
      const responseDivs_C = document.querySelectorAll(
        '.crimeCommCheck-responses, .oneYearCheck-responses, .leftCountryCheck-responses,' +
        '.causedHarmCheck-responses, .inCountry-responses, .prevApplCheck-responses'
      );
      function handlePartCRadioChange() {
        responseDivs_C.forEach(div => {
          div.style.display = 'none';
        });
        partCRadioButtons.forEach(radio => {
          if (radio.name === "lawfulStatus" || radio.name === "inCountry") {
            if (radio.checked && radio.value === 'yes') {
              const inCountryDiv = document.querySelector('.inCountry-responses');
              if (inCountryDiv) {
                inCountryDiv.style.display = 'block';
              }
            }
          } else if (radio.checked && radio.value === 'yes') {
            const responseDivId = `.${radio.name}-responses`;
            const responseDiv = document.querySelector(responseDivId);
            if (responseDiv) {
              responseDiv.style.display = 'block';
            }
          }
        });
      }
      partCRadioButtons.forEach(radio => {
        radio.addEventListener('change', handlePartCRadioChange);
      });
      handlePartCRadioChange();


      const assistanceCheckRadios = document.querySelectorAll('input[name="assistanceCheck"]');
      const assistantListDiv = document.querySelector('.assistant-list');
      const assistant_requiredElements = assistantListDiv.querySelectorAll(".required");
      function toggleAssistantList(event = { target: assistanceCheckRadios[0] }) {
        const selectedRadio = event.target;
        if (selectedRadio.checked && selectedRadio.value === 'yes') {
          assistantListDiv.style.display = 'block';
          assistant_requiredElements.forEach(element => {
            if (!element.classList.contains('required')) {
              element.classList.add('required');
            }
          });
        } else {
          assistantListDiv.style.display = 'none';
          assistant_requiredElements.forEach(element => {
            if (element.classList.contains('required')) {
              element.classList.remove('required');
            }
          });
        }
      }
      assistanceCheckRadios.forEach(radio => {
        radio.addEventListener('change', toggleAssistantList);
      });
      toggleAssistantList();
      const addAssistantButton = document.getElementById("add-assistant");
      const assistantContainer = document.querySelector('assistant-list');
      let assistantCounter = 0;
      addAssistantButton.addEventListener('click', () => {
        assistantCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const assistantDiv = document.createElement('div');
        assistantDiv.classList.add('assistant');
        assistantDiv.id = `assistant-${assistantCounter}`;
        assistantDiv.innerHTML = `
                <div class="divided-text" id="one-one">
                <div class="text-input" id="full-width">
                    <label for="d-assistName-${assistantCounter}" id="text-box" class="required">Name</label>
                    <input type="text" id="d-assistName-${assistantCounter}" class="textbox required">
                </div>
                <div class="text-input" id="full-width">
                    <label for="d-relationship-${assistantCounter}" id="text-box" class="required">Relationship</label>
                    <input type="text" id="d-relationship-${assistantCounter}" class="textbox required">
                </div>
                </div>
                `;
        const addEntriesDiv = addAssistantButton.parentNode;
        addEntriesDiv.insertBefore(separatorDiv, addAssistantButton);
        addEntriesDiv.insertBefore(assistantDiv, addAssistantButton);
      });

      const marriedToggle = document.querySelector("input[id='spouseCheck']");
      const spouseDiv = document.querySelector(".spouse");
      const spouse_requiredElements = spouseDiv.querySelectorAll(".required");
      const childrenToggle = document.querySelector("input[id='childrenCheckInp']");
      const childrenDiv = document.querySelector('.children');
      const children_requiredElements = childrenDiv.querySelectorAll(".required");
      function toggleSpouseInfo() {
        if (marriedToggle.checked) {
          spouseDiv.style.display = "none";
          spouse_requiredElements.forEach(element => {
            if (element.classList.contains('required')) {
              element.classList.remove('required');
            }
          })
        } else {
          spouseDiv.style.display = "block";
          spouse_requiredElements.forEach(element => {
            if (!element.classList.contains('required')) {
              element.classList.add('required');
            }
          })
        }
      }

      function toggleChildrenInfo() {
        if (childrenToggle.checked) {
          childrenDiv.style.display = "none";
          children_requiredElements.forEach(element => {
            if (element.classList.contains('required')) {
              element.classList.remove('required');
            }
          })
        } else {
          childrenDiv.style.display = "block";
          children_requiredElements.forEach(element => {
            if (!element.classList.contains('required')) {
              element.classList.add('required');
            }
          })
        }
      }
      marriedToggle.addEventListener('change', toggleSpouseInfo);
      childrenToggle.addEventListener('change', toggleChildrenInfo);
      toggleSpouseInfo();
      toggleChildrenInfo();

      const addChildrenButton = document.getElementById("add-children");
      const childrenContainer = document.querySelector(".children");
      let childCounter = 0;

      addChildrenButton.addEventListener('click', () => {
        childCounter++;
        const separatorDiv = document.createElement('div');
        separatorDiv.classList.add('midsubsection-seperator');
        const childDiv = document.createElement('div');
        childDiv.classList.add('child');
        childDiv.id = `child-${childCounter}`;
        childDiv.innerHTML = `
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-firstName" id="text-box" class="required">First Name</label> <input type="text"
                        id="a-ii-child-${childCounter}-firstName" class="textbox required">
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-middleName" id="text-box">Middle Name</label> <input type="text"
                        id="a-ii-child-${childCounter}-middleName" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-lastName" id="text-box" class="required">Complete Last Name</label> <input type="text"
                        id="a-ii-child-${childCounter}-lastName" class="textbox required">
                    </div>
                    <div class="divided-text" id="one-three">
                    <div class="radio-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-gender" id="text-box" class="required">Gender:</label>
                        <div class="radio-group required">
                        <div class="radio-set">
                            <input type="radio" value="male" name="child-${childCounter}-gender" id="a-ii-child-${childCounter}-gender"> <label for="male" id="radio-set">Male</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="female" name="child-${childCounter}-gender" id="a-ii-child-${childCounter}-gender"> <label for="female"
                            id="radio-set">Female</label>
                        </div>
                        </div>
                    </div>
                    <div class="radio-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-maritalSts" id="text-box" class="required">Marital Status:</label>
                        <div class="radio-group required">
                        <div class="radio-set">
                            <input type="radio" value="single" name="child-${childCounter}-maritalSts" id="a-ii-child-${childCounter}-maritalSts"> <label for="single"
                            id="radio-set">Single</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="married" name="child-${childCounter}-maritalSts" id="a-ii-child-${childCounter}-maritalSts"> <label for="married"
                            id="radio-set">Married</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="divorced" name="child-${childCounter}-maritalSts" id="a-ii-child-${childCounter}-maritalSts"> <label for="divorced"
                            id="radio-set">Divorced</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="widowed" name="child-${childCounter}-maritalSts" id="a-ii-child-${childCounter}-maritalSts"> <label for="widowed"
                            id="radio-set">Widowed</label>
                        </div>
                        </div>
                    </div>
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-anumber" id="text-box">Alien Registration Number(s) (A-Number) (if
                        any)</label> <input type="text" id="a-ii-child-${childCounter}-anumber" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-ssn" id="text-box">US Social Security Number (if any)</label>
                    <input type="text" id="a-ii-child-${childCounter}-ssn" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-id" id="text-box">Passport/ID Card Number (if any)</label> <input type="text"
                        id="a-ii-child-${childCounter}-id" class="textbox">
                    </div>
                    <div class="divided-text" id="one-three">
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-dob" id="text-box" class="required">Date of Birth</label>
                        <input type="date"
                        id="a-ii-child-${childCounter}-dob" class="textbox required">
                    </div>
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-ccob" id="text-box" class="required">City and Country of Birth</label> <input type="text"
                        id="a-ii-child-${childCounter}-ccob" class="textbox required">
                    </div>
                    </div>
                    <div class="divided-text" id="three-three-three">
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-citizenship" id="text-box" class="required">Nationality (Citizenship)</label>
                        <input type="text" id="a-ii-child-${childCounter}-citizenship" class="textbox required">
                    </div>
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-race" id="text-box" class="required">Race, Ethnic or Tribal Group</label> <input type="text"
                        id="a-ii-child-${childCounter}-race" class="textbox required">
                    </div>
                    </div>
                    <div class="radio-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-UScheck" id="text-box" class="required">Is this child in the U.S.?</label>
                    <div class="radio-group required">
                        <div class="radio-set">
                        <input type="radio" value="yes" name="child-${childCounter}-childUS" id="a-ii-child-${childCounter}-UScheck"> <label for="yes" id="radio-set">Yes</label>
                        </div>
                        <div class="radio-set">
                        <input type="radio" value="no" name="child-${childCounter}-childUS" id="a-ii-child-${childCounter}-UScheck"> <label for="no" id="radio-set">No</label>
                        </div>
                    </div>
                    </div>
                    <div class="a-ii-child-${childCounter}-loc">
                      <div class="text-input" id="full-width">
                      <label for="a-ii-child-${childCounter}-loc" id="text-box">Specify this child's location</label> <input type="text"
                          id="a-ii-child-${childCounter}-loc" class="textbox">
                      </div>
                    </div>
                    <div class="divided-text" id="one-three">
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-lastEntry-date" id="text-box">Date of last entry into the
                        US</label> <input type="date" id="a-ii-child-${childCounter}-lastEntry-date" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-lastEntry-place" id="text-box">Place of last entry into the
                        US</label> <input type="text" id="a-ii-child-${childCounter}-lastEntry-place" class="textbox">
                    </div>
                    </div>
                    <div class="divided-text" id="three-three-three">
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-i94" id="text-box">I-94 Number (if any)</label> <input type="text"
                        id="a-ii-child-${childCounter}-i94" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-lastEntry-status" id="text-box">Status when last admitted (Visa
                        type, if any)</label> <input type="text" id="a-ii-child-${childCounter}-lastEntry-status" class="textbox">
                    </div>
                    <div class="text-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-currSts" id="text-box" class="required">Current status</label> <input type="text"
                        id="a-ii-child-${childCounter}-currSts" class="textbox required">
                    </div>
                    </div>
                    <div class="text-input" id="full-width">
                    <label for="a-ii-child-${childCounter}-currExp" id="text-box">What is the expiration date of his/her
                        authorized stay, if any?</label>
                        <input type="date" id="a-ii-child-${childCounter}-currExp" class="textbox">
                    </div>
                    <div class="divided-text" id="one-one">
                    <div class="radio-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-immiProc" id="text-box" class="required">Is your child in Immigration Court
                        proceedings</label>
                        <div class="radio-group required">
                        <div class="radio-set">
                            <input type="radio" value="yes" name="child-${childCounter}-immiProc" id="a-ii-child-${childCounter}-immiProc"> <label for="yes" id="radio-set">Yes</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="no" name="child-${childCounter}-immiProc" id="a-ii-child-${childCounter}-immiProc"> <label for="no" id="radio-set">No</label>
                        </div>
                        </div>
                    </div>
                    <div class="radio-input" id="full-width">
                        <label for="a-ii-child-${childCounter}-inclusion" id="text-box">If in the U.S., is this child to be
                        included in this application</label>
                        <div class="radio-group">
                        <div class="radio-set">
                            <input type="radio" value="yes" name="child-${childCounter}-inclusion" id="a-ii-child-${childCounter}-inclusion"> <label for="yes" id="radio-set">Yes</label>
                        </div>
                        <div class="radio-set">
                            <input type="radio" value="no" name="child-${childCounter}-inclusion" id="a-ii-child-${childCounter}-inclusion"> <label for="no" id="radio-set">No</label>
                        </div>
                        </div>
                    </div>
                    </div>
                `;
        childrenContainer.insertBefore(separatorDiv, addChildrenButton);
        childrenContainer.insertBefore(childDiv, addChildrenButton);
      });



      DsignInput.addEventListener('click', () => {
        DhiddenFileInput.click();
      });

      DhiddenFileInput.addEventListener('change', () => {
        const DselectedFile = DhiddenFileInput.files[0];
        DsignInput.style.borderStyle = 'solid';
        DsignTitle.style.display = 'none';
        DsignSubtitle.style.display = 'none';
        DsignSelected.style.display = 'block';
        DsignSelected.textContent += `${DselectedFile.name}`;
      });
      function handlePartChange(event) {
        const partDropdown = event.target;
        const additionalEntry = partDropdown.closest('.suppAB-additional');
        const questionDropdown = additionalEntry.querySelector('select[name="question"]');
        const questionOptions = Array.from(questionDropdown.options);

        const selectedPart = `${partDropdown.value}-`;
        questionOptions.forEach(option => {
          const shouldShow = selectedPart === 'start' || option.value.includes(selectedPart);
          option.style.display = shouldShow ? 'block' : 'none';
        });
      }
    } else if (clickedButton.id == 'user') {
      hideAll();
      const loginCookie = getCookie('username');
      if (loginCookie != null) {
        const userPage = document.getElementById("profile-container");
        if (!userPage) {
          const { username, firstName, lastName, email, profilePicUrl, user_location } = loginCookie;
          showUserPage(username, firstName, lastName, email, profilePicUrl, user_location);
        } else {
          userPage.setAttribute('style', 'display: flex;');
        }
        const loginWindow = document.getElementById("login-window");
        loginWindow.setAttribute('style', 'display: none;');
      } else {
        showLoginWindow();
      }
      const chatButton = document.getElementById('chat');
      chatButton.removeAttribute('style');
    }
  }
}

function showDisclaimer() {
  document.querySelector('.disclaimer').style.display = 'flex';
}

function closeDisclaimer() {
  document.querySelector('.disclaimer').style.display = 'none';
}


async function createLoginCookie(username, firstName, lastName, email, profilePicUrl, user_location = null) {
  const data = await getProfilePic(email);
  let newProfilePic;
  if (data.result) {
    newProfilePic = data.profilePic;
  } else {
    newProfilePic = profilePicUrl;
  }
  user_location = user_location || '';
  const expirationDate = new Date();
  expirationDate.setDate(expirationDate.getDate() + 14);
  const cookieValue = `username=${username}|${firstName}|${lastName}|${email}|${user_location}|${newProfilePic}; expires=${expirationDate.toUTCString()}; path=/`;
  document.cookie = cookieValue;
}

function attachSignin(element) {
  auth2.attachClickHandler(element, {},
    function (googleUser) {
      const profile = googleUser.getBasicProfile();
      const email = profile.getEmail();
      const username = email.split('@')[0];
      const firstName = profile.getGivenName();
      const lastName = profile.getFamilyName();
      const profilePicUrl = profile.getImageUrl();
      createLoginCookie(username, firstName, lastName, email, profilePicUrl, user_location = null);
      document.getElementById("login-window").setAttribute("style", "display: none");
      showUserPage(username, firstName, lastName, email, profilePicUrl, user_location = null)
    });
}

function addUser(backendUrl, firstName, lastName, email, username, user_location = null, password = null, profilePic = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png") {
  fetch(`${backendUrl}new_user/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ firstName, lastName, email, username, user_location, password, profilePic })
  })
    .then(response => {
      if (!response.ok) {
        console.log('Error adding user: ', response.status);
      }
    })
    .catch(error => {
      console.log('Error: ', error)
    })

}



buttons.forEach(button => button.addEventListener('click', () => setActiveButton(button)));





async function handlePlanButtonClick(event) {
  const button = event.target;
  const tier = button.parentElement.querySelector('h3').id;
  const duration = document.querySelector('input[name="plan-duration"]:checked').value;
  const email = getCookie('username').email;
  try {
    const response = await fetch(`${backendUrl}create_checkoutsess/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tier, duration, email })
    });

    const data = await response.json();
    const stripe = Stripe('pk_live_51PDwGXP6cNlgDSsmbpqe2mJUE2oYznCtT4AWzvNewWy2s1senClvQdBpGo7vhnnEmitiAIDHEqMszvg5bBPt7wEN00sHnbYPnG');

    await stripe.redirectToCheckout({
      sessionId: data.id
    });
  } catch (error) {
    console.error('Error:', error);
  }
}

function loadTabContent(tab, userData) {
  const contentDiv = document.querySelector(`#${tab}`);
  contentDiv.innerHTML = '';
  switch (tab) {
    case 'profile':
      loadProfileContent(contentDiv, userData);
      break;
    case 'files':
      loadFilesContent(contentDiv);
      break;
    case 'lawyers':
      loadLawyersContent(contentDiv);
      break;
    case 'support':
      loadSupportContent(contentDiv);
      break;
    case 'forms':
      loadFormsContent(contentDiv);
      break;
  }
}

function updateUserData(firstName, lastName, username, user_location, profilePicUrl = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png", email_id = getCookie('username').email) {
  fetch(`${backendUrl}update_user/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email_id, firstName, lastName, username, user_location, profilePicUrl })
  })
    .then(response => response.json())
    .then(data => {
      console.log('User Data Updated!');
    })
    .catch(error => console.error(error));

}

function loadProfileContent(contentDiv, userData) {
  user_location = userData.user_location || '';
  const profileForm = document.createElement('form');
  profileForm.className = 'userPage'
  profileForm.innerHTML = `
    <h2 class="pagetitle">Main Information</h2>
    <div class="userDets">
        <div class="profilePic">
            <input type="file" id="profilePicInput" accept="image/png, image/jpeg" style="display: none;">
                <label for="profilePicInput" style="cursor: pointer;">                
                    <canvas id="profilePicCanvas" width="175" height="175" style="background-image: url('${userData.profilePic}');"></canvas>
                </label>
            <a class="profilePicText">Click to Change</a>
        </div>
        <div class="userDetsText">
            <label>Username: <input id="username" type="text" value="${userData.username}"></label>
            <p id="usernameError" class="error"></p>
            <div class="userName">
                <label>First Name: <input id="firstname" type="text" value="${userData.firstName}"></label>
                <label>Last Name: <input id="lastname" type="text" value="${userData.lastName}"></label>
            </div>
            <label>Location: <input id="location" type="text" value="${user_location}"></label>
        </div>
    </div>
    <div class="profileButtons">
        <button type="button" id="subscribe" onclick="subscription();">Upgrade</button>
        <button type="submit" id="saveChanges" style="display: none;">Save Changes</button>
        <button type="button" id="changePassword">Change Password</button>
        
    </div>
  `;

  const changePasswordBtn = profileForm.querySelector('#changePassword');
  changePasswordBtn.addEventListener('click', () => {
    showPasswordForm()
  });

  const saveChangesBtn = profileForm.querySelector('#saveChanges');
  const email_id = userData.email;
  const newUsername = profileForm.querySelector('#username');
  const newUsernameError = profileForm.querySelector('#usernameError')
  const firstNameInput = profileForm.querySelector('#firstname')
  const lastNameInput = profileForm.querySelector('#lastname')
  const locationInput = profileForm.querySelector('#location')
  let newProfilePic = userData.profilePic;
  const profilePicInput = profileForm.querySelector('#profilePicInput');
  const profilePicCanvas = profileForm.querySelector("#profilePicCanvas");
  profilePicInput.addEventListener('change', () => {
    saveChangesBtn.disabled = true;
    updateProfilePic(profilePicInput, profilePicCanvas);
    const file = profilePicInput.files[0];
    const formData = new FormData();
    formData.append('profilePic', file)
    formData.append('email_id', email_id)

    fetch(`${backendUrl}uploadProfilePic/`, {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.resp) {
          newProfilePic = data.url
        }
        else {
          console.log('Error uploading the pic: ', data.error)
        }
      })
      .catch(error => {
        console.error('Error uploading the pic: ', error);
      })
      .finally(() => {
        saveChangesBtn.disabled = false;
      });
  });

  const inputFields = profileForm.querySelectorAll('input');
  inputFields.forEach(input => {
    input.addEventListener('input', () => {
      saveChangesBtn.style.display = 'inline-block';
    });
  });

  newUsername.addEventListener('change', () => {
    checkUsername(saveChangesBtn, newUsername.value, newUsernameError);
  })

  saveChangesBtn.addEventListener('click', (e) => {
    e.preventDefault();
    updateUserData(firstNameInput.value, lastNameInput.value, newUsername.value, locationInput.value, newProfilePic);
    const newProfilePicUrl = `https://doloreschatbucket.s3.us-east-2.amazonaws.com/users/${newUsername.value}/profilePic/user.png`
    createLoginCookie(newUsername.value, firstNameInput.value, lastNameInput.value, email_id, newProfilePicUrl, locationInput.value);
    saveChangesBtn.style.display = 'none';
  })

  contentDiv.appendChild(profileForm);
}

function showPasswordForm() {
  const profileForm = document.querySelector('#profile form');
  const contentDiv = document.getElementById('profile');
  const passwordForm = document.createElement('div');
  passwordForm.className = 'updPass'
  passwordForm.innerHTML = `
    <h2 class="passtitle">New Password</h2>
    <div class="passText">
        <label>New Password: <input id="password" type="password"></label>
        <label>Confirm Password: <input id="Confpassword" type="password"></label>
    </div>
    <p id="passwordError" class="error"></p>
    <div class="newPassButt">
        <button type="button" id="savePassword">Save Password</button>
        <button type="button" id="cancelPassword">Cancel</button>
    </div>
  `;
  const passwordInput = passwordForm.querySelector("#password");
  const confirmPasswordInput = passwordForm.querySelector("#Confpassword");
  const passwordError = passwordForm.querySelector("#passwordError");
  const savePasswordBtn = passwordForm.querySelector('#savePassword');
  passwordInput.addEventListener('input', () => {
    validatePassword(passwordInput.value, confirmPasswordInput.value, passwordError, savePasswordBtn);
  });
  confirmPasswordInput.addEventListener('input', () => {
    validatePassword(passwordInput.value, confirmPasswordInput.value, passwordError, savePasswordBtn);
  });
  savePasswordBtn.addEventListener('click', () => {
    saveNewPassword(passwordInput.value)
  });

  const cancelBtn = passwordForm.querySelector('#cancelPassword');
  cancelBtn.addEventListener('click', () => {
    passwordForm.remove();
    const profileForm = document.querySelector('#profile form');
    profileForm.style.display = 'block';
  });

  profileForm.style.display = 'none';
  contentDiv.appendChild(passwordForm);
}

function saveNewPassword(password) {
  const email_id = getCookie('username').email
  fetch(`${backendUrl}update_password/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email_id, password })
  })
    .then(response => response.json())
    .then(data => {
      console.log('User Password Updated!');
    })
    .catch(error => console.error(error));

  const passwordForm = document.querySelector('.updPass');
  passwordForm.remove();

  const profileForm = document.querySelector('#profile form');
  profileForm.style.display = 'block';
}



async function loadFilesContent(contentDiv) {
  let filesData = await getFiles('files') || [];

  const gridContainer = document.createElement('div');
  const gridTitle = document.createElement('h2');
  gridTitle.classList.add('filesList');
  gridTitle.textContent = 'Your Files';

  const filesContainer = document.createElement('div');
  filesContainer.classList.add('files-container');
  filesData.forEach(file => {
    const fileTile = document.createElement('div');
    fileTile.classList.add('file-tile');

    const fileLink = document.createElement('a');
    fileLink.href = file.url;
    fileLink.target = '_blank';
    fileLink.classList.add('file-link');

    const fileImage = document.createElement('div');
    fileImage.classList.add('file-image');
    fileImage.style.backgroundImage = `url('${file.thumbnail}')`;

    const fileTitle = document.createElement('div');
    fileTitle.classList.add('file-title');
    fileTitle.textContent = file.title;

    fileLink.appendChild(fileImage);
    fileLink.appendChild(fileTitle);
    fileTile.appendChild(fileLink);
    filesContainer.appendChild(fileTile);
  });

  const addTile = document.createElement('div');
  addTile.classList.add('file-tile', 'add-tile');

  const addIcon = document.createElement('div');
  addIcon.classList.add('add-icon');
  addIcon.textContent = '+';

  const addTitle = document.createElement('div');
  addTitle.classList.add('add-title');
  addTitle.textContent = 'Add from Local Storage';

  addTile.appendChild(addIcon);
  addTile.appendChild(addTitle);
  filesContainer.appendChild(addTile);

  gridContainer.appendChild(gridTitle);
  gridContainer.appendChild(filesContainer);
  contentDiv.appendChild(gridContainer);
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.multiple = true;
  fileInput.style.display = 'none';
  addTile.addEventListener('click', () => {
    fileInput.click();
    console.log('Adding items from local storage');
  });

  fileInput.addEventListener('change', async (event) => {
    const files = fileInput.files;
    const formData = new FormData();
    const email_id = getCookie('username').email;
    for (const file of files) {
      formData.append('files', file);
      formData.append('flag', 'files');
      formData.append('email_id', email_id);
    }

    try {
      const response = await fetch(`${backendUrl}upload_files/`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        console.log('Files uploaded successfully');
        loadTabContent('files')
      } else {
        console.error('Error uploading files');
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  });
}

async function getProfilePic(email_id) {
  try {
    const response = await fetch(`${backendUrl}get_profilePic/`, {
      method: 'POST',
      body: JSON.stringify({ email_id })
    });

    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Error:', error);
  }
}

async function getFiles(flag) {
  const formData = new FormData();
  const email_id = getCookie('username').email;
  formData.append('email_id', email_id);
  formData.append('flag', flag)
  try {
    const response = await fetch(`${backendUrl}get_filesList/`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      console.error(`HTTP error! Status: ${response.status}`)
    }
    const filesData = await response.json();
    const fileData = filesData.map(file => ({
      title: file.title,
      url: file.url,
      thumbnail: file.thumbnail
    }));
    return fileData;
  } catch (error) {
    console.error('Error fetching files: ', error)
  }
}

function loadLawyersContent(contentDiv) {
  // Fetch lawyers data from the backend
  const lawyersData = [
    // { title: 'Lawyer 1', url: 'lawyer1.html', thumbnail: 'lawyer1.jpg' },
    // { title: 'Lawyer 2', url: 'lawyer2.html', thumbnail: 'lawyer2.jpg' },
    // ... add more lawyers
  ];

  const gridContainer = document.createElement('div');
  const gridTitle = document.createElement('h2');
  gridTitle.classList.add('lawyersList');
  gridTitle.textContent = 'Lawyer List';

  const lawyersContainer = document.createElement('div');
  lawyersContainer.classList.add('lawyers-container');
  lawyersData.forEach(lawyer => {
    const lawyerTile = document.createElement('div');
    lawyerTile.classList.add('lawyer-tile');

    const lawyerLink = document.createElement('a');
    lawyerLink.href = lawyer.url;
    lawyerLink.target = '_blank';
    lawyerLink.classList.add('lawyer-link');

    const lawyerImage = document.createElement('div');
    lawyerImage.classList.add('lawyer-image');
    lawyerImage.style.backgroundImage = `url('${lawyer.thumbnail}')`;

    const lawyerTitle = document.createElement('div');
    lawyerTitle.classList.add('lawyer-title');
    lawyerTitle.textContent = lawyer.title;

    lawyerLink.appendChild(lawyerImage);
    lawyerLink.appendChild(lawyerTitle);
    lawyerTile.appendChild(lawyerLink);
    lawyersContainer.appendChild(lawyerTile);
  });

  gridContainer.appendChild(gridTitle);
  gridContainer.appendChild(lawyersContainer);

  contentDiv.appendChild(gridContainer);
}

function loadSupportContent(contentDiv) {
  const userEmail = getCookie('username').email;

  const supportForm = document.createElement('form');
  supportForm.classList.add('supportFormIncl')
  supportForm.innerHTML = `
    <h2 class="supporttitle">Support Form</h2>
    <div class="supportForm">
        <label id="supportEmail">Email: <input id="supportEmail" type="email" value="${userEmail}" disabled></label>
        <label id="supportSubj">Subject: <input id="supportSubj" type="text" placeholder="Enter subject"></label>
        <label id="supportMsg">Message: <textarea rows="6" id="supportMsg" placeholder="Enter your message"></textarea></label>
    </div>
    <div class="supportButton">
        <button id="supportSubmit" type="submit">Submit</button>
    </div>
  `;

  supportForm.addEventListener('submit', e => {
    e.preventDefault();
    const subject = supportForm.querySelector('input[type="text"]').value;
    const message = supportForm.querySelector('textarea').value;
    // ... send subject and message to the backend
    alert('Support request submitted successfully!');
    supportForm.reset();
  });

  contentDiv.appendChild(supportForm);
}

async function loadFormsContent(contentDiv) {
  let formsData = await getFiles('forms') || [];
  const gridContainer = document.createElement('div');
  const gridTitle = document.createElement('h2');
  gridTitle.classList.add('formsList');
  gridTitle.textContent = 'Your Forms';

  const formsContainer = document.createElement('div');
  formsContainer.classList.add('forms-container');
  formsData.forEach(form => {
    const formTile = document.createElement('div');
    formTile.classList.add('form-tile');

    const formLink = document.createElement('a');
    formLink.href = form.url;
    formLink.target = '_blank';
    formLink.classList.add('form-link');

    const formImage = document.createElement('div');
    formImage.classList.add('form-image');
    formImage.style.backgroundImage = `url('${form.thumbnail}')`;

    const formTitle = document.createElement('div');
    formTitle.classList.add('form-title');
    formTitle.textContent = form.title;

    formLink.appendChild(formImage);
    formLink.appendChild(formTitle);
    formTile.appendChild(formLink);
    formsContainer.appendChild(formTile);
  });

  const addTile = document.createElement('div');
  addTile.classList.add('form-tile', 'add-tile');

  const addIcon = document.createElement('div');
  addIcon.classList.add('add-icon');
  addIcon.textContent = '+';

  const addTitle = document.createElement('div');
  addTitle.classList.add('add-title');
  addTitle.textContent = 'Add from Local Storage';

  addTile.appendChild(addIcon);
  addTile.appendChild(addTitle);
  formsContainer.appendChild(addTile);

  gridContainer.appendChild(gridTitle);
  gridContainer.appendChild(formsContainer);

  contentDiv.appendChild(gridContainer);

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.multiple = true;
  fileInput.style.display = 'none';

  addTile.addEventListener('click', () => {
    fileInput.click();
    console.log('Adding items from local storage');
  });

  fileInput.addEventListener('change', async (event) => {
    const files = event.target.files;
    const formData = new FormData();
    const email_id = getCookie('username').email;
    for (const file of files) {
      formData.append('files', file);
      formData.append('flag', 'forms');
      formData.append('email_id', email_id);
    }

    try {
      const response = await fetch(`${backendUrl}upload_files/`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        console.log('Forms uploaded successfully');
        loadTabContent('forms')
      } else {
        console.error('Error uploading files');
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  });
}
