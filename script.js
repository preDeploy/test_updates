const buttons = document.querySelectorAll('.button');
const chatHistory = document.querySelector('.chat-container');
const messageInput = document.getElementById('user-input');
const sendButton = document.getElementById('send');
const chatWindow = document.querySelector('.chat-bar-container');
const formWindow = document.querySelector('.form-container');
const chatMessages = document.querySelector('.chat-messages');
const mainDownload = document.getElementById('download');
const mainShare = document.getElementById('share');
const form = document.getElementById('immigrationForm');
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
const tabLinks = document.querySelectorAll('.sidebar a');
const tabContents = document.querySelectorAll('.content .tab');
const emailInput = document.getElementById('emailInput');
const emailButton = document.getElementById('emailButton');
const googleButton = document.getElementById('googleButton');
const loginContainer = document.querySelector('.login-window')

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        const cookieData = parts.pop().split(';').shift();
        const [username, firstName, lastName, email, profilePicUrl, location] = cookieData.split('|');
        return { username, firstName, lastName, email, profilePicUrl, location };
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

// async function showUserPage() {
//     document.getElementById("login-window").style.display = "none";
//     const subscription = await getSubscription();
//     const userTierElement = document.getElementById('user-tier');
//     userTierElement.textContent = subscription
//     loadTabContent('profile');
//     document.getElementById("userPage").style.display = "block";
//     document.getElementById("form").removeAttribute('style');

// }

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
    // const password = regPasswordInput.value;
    // const confirmPassword = confirmPasswordInput.value;
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
    // const username = usernameInput.value;
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
    // profilePicInput.addEventListener('click', () => profilePicInput.click());
    profilePicInput.addEventListener('change', ()=>{
        updateProfilePic(profilePicInput, profilePicCanvas)
        const file = profilePicInput.files[0];
        formData.append('profilePic', file)
        formData.append('email_id', email)     
        
    });
    doneButton.addEventListener('click', () => {
        registerUser(email, firstNameInput.value, lastNameInput.value, regPasswordInput.value, usernameInput.value, locationInput.value);
        fetch(`${backendUrl}uploadProfilePic/`, {
            method: 'POST',
            body: formData
        })
        .then(response  => response.json())
        .then(data => {
            if (data.resp){
                newProfilePic = data.url;
            }
            else {
                
                console.log('Error uploading the pic: ', data.error)
            }
        })
        .then(() => {
            createLoginCookie(usernameInput.value, firstNameInput.value, lastNameInput.value, email, newProfilePic, locationInput.value);
            loginContainer.setAttribute('style', 'display: none;');
            showUserPage(usernameInput.value, firstNameInput.value, lastNameInput.value, email, newProfilePic, locationInput.value);
        })
        .catch(error => {
            console.error('Error uploading the pic: ', error);
        });
        
    });


}

function registerUser(email, firstName, lastName, password, username, location = "", profilePic = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png") {
    // const regEmailInput = document.getElementById('regEmailInput');
    // const firstNameInput = document.getElementById('firstNameInput');
    // const lastNameInput = document.getElementById('lastNameInput');
    // const regPasswordInput = document.getElementById('regPasswordInput');
    // const locationInput = document.getElementById('locationInput');
    // const profilePicInput = document.getElementById('profilePicInput');

    // // console.log(regEmailInput)

    // const email = regEmailInput.value;
    // const firstName = firstNameInput.value;
    // const lastName = lastNameInput.value;
    // const password = regPasswordInput.value;
    // const location = locationInput.value;
    // const profilePic = profilePicInput.files[0];
    // console.log(profilePic)

    // const formData = new FormData();
    const formData = { email, firstName, lastName, password, location, profilePic, username }
    // formData.append('email', email);
    // formData.append('firstName', firstName);
    // formData.append('lastName', lastName);
    // formData.append('password', password);
    // formData.append('location', location);
    // formData.append('profilePic', profilePic);

    fetch(`${backendUrl}register/`, {
        method: 'POST',
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            console.log('User Registered!');
            // Handle successful registration
        })
        .catch(error => console.error(error));
}

// function startApp() {
//     gapi.load('auth2', function () {
//       auth2 = gapi.auth2.init({
//         client_id: "699627421105-5b2u0uckdbqievn40vjto4l04ih7v4pq.apps.googleusercontent.com",
//         cookiepolicy: 'single_host_origin',
//         plugin_name: "Dolores_Login",
//       });
//       attachSignin(document.getElementById('customBtn'));
//     });
//   }

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
    const emailInput = document.getElementById('emailInput');
    const emailButton = document.getElementById('emailButton');
    const googleButton = document.getElementById('googleButton');

    // emailButton.addEventListener('click', checkUser);
    // googleButton.addEventListener('click', startApp);
}

// function signInWithGoogle() {
//     // Implement Google Sign-In functionality
//     console.log('Sign in with Google');
// }

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
                const { username, firstName, lastName, email, profilePicUrl, location } = data;
                createLoginCookie(username, firstName, lastName, email, profilePicUrl, location);
                document.getElementById("login-window").setAttribute("style", "display: none");
                showUserPage(username, firstName, lastName, email, profilePicUrl, location)

            }

        })
        .catch(error => console.error(error));



    // Implement login functionality
    // console.log('Login with email:', email, 'and password:', password);
}

function showUserPage(username, firstName, lastName, email, profilePicUrl, location) {
    const profileContainer = document.getElementById('profile-container');
    profileContainer.removeAttribute('style');
    const tabLinks = document.querySelectorAll('.sidebar a');
    const tabContents = document.querySelectorAll('.content .tab');

    const userData = {
        profilePic: profilePicUrl,
        username: username,
        firstName: firstName,
        lastName: lastName,
        location: location,
        email: email
    };
    tabLinks.forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const targetTab = e.target.getAttribute('data-tab');

            // Remove active class from all links and content divs
            tabLinks.forEach(link => link.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked link and corresponding content div
            e.target.classList.add('active');
            document.getElementById(targetTab).classList.add('active');

            // Load content for the selected tab
            loadTabContent(targetTab, userData);
        });
    });
    loadTabContent('profile', userData);
    document.getElementById("form").removeAttribute('style');
    addUser(backendUrl, firstName, lastName, email, username, location, password=null, profilePic=profilePicUrl);


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
                buttons[i].textContent = 'Subscribe';
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
    // loadTabContent('profile', userData);

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
    document.getElementById("login-window").setAttribute("style", "display: none");
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

function setActiveButton(clickedButton) {
    buttons.forEach(button => button.classList.remove('active'));
    const parentClassList = clickedButton.parentElement.classList;
    if (parentClassList.contains("side-container") || parentClassList.contains("menu-container") || parentClassList.contains("chat-bar-container")) {
        clickedButton.classList.add('active');
        if (clickedButton.id == 'chat') {
            hideAll();
            if (!chatWindow.classList.contains('active')) {
                chatWindow.classList.add('active');
            }
            if (!chatHistory.classList.contains('active')) {
                chatHistory.classList.add('active');
            }
            document.getElementById("disclaimer").removeAttribute('style');
        } else if (clickedButton.id == 'form') {
            hideAll();
            if (!formWindow.classList.contains('active')) {
                formWindow.classList.add('active');
            }
            mainDownload.removeAttribute('style');
            mainShare.removeAttribute('style');
            let mainInfo = {};
            let spouseChildInfo = {};

            form.addEventListener('input', function () {
                const totalFields = form.querySelectorAll('input').length;
                const filledFields = form.querySelectorAll('input:valid').length;
                const progress = (filledFields / totalFields) * 100;
                progressBar.style.width = progress + '%';
            });

            nextButton.addEventListener('click', function (event) {
                event.preventDefault();
                mainInfo = {
                    firstName: document.getElementById('firstName').value,
                    middleName: document.getElementById('middleName').value,
                    lastName: document.getElementById('lastName').value,
                    // Add other fields as required
                };
                form.reset();
                document.querySelector('.sub-heading').textContent = 'Spouse/Child Information';
                nextButton.style.display = 'none';
                submitButton.removeAttribute("style");
            });

            submitButton.addEventListener('click', function (event) {
                event.preventDefault();
                spouseChildInfo = {
                    firstName: document.getElementById('firstName').value,
                    middleName: document.getElementById('middleName').value,
                    lastName: document.getElementById('lastName').value,
                    // Add fields for spouse/child information
                };
                const combinedInfo = {
                    ...mainInfo,
                    ...spouseChildInfo
                };
                const combinedInfoJson = JSON.stringify(combinedInfo);
                form.style.display = 'none';
                downloadForm.style.display = 'flex';
                downloadForm.querySelector('input[name="data"]').value = combinedInfoJson;
            });

            downloadButton.addEventListener('click', function () {
                const combinedInfoJson = downloadForm.querySelector('input[name="data"]').value;
                console.log(combinedInfoJson)
                const blob = new Blob([combinedInfoJson], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'immigration_info.json';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            });

            differentAddressCheckbox.addEventListener('change', function () {
                mailingAddressSection.classList.toggle('hidden');
            });
            // });
        } else if (clickedButton.id == 'user') {
            hideAll();
            const loginCookie = getCookie('username');
            if (loginCookie != null) {
                const userPage = document.getElementById("profile-container");
                if (!userPage) {
                    const { username, firstName, lastName, email, profilePicUrl, location } = loginCookie;
                    showUserPage(username, firstName, lastName, email, profilePicUrl, location);
                    // const userData = {
                    //     profilePic: profilePicUrl,
                    //     username: username,
                    //     firstName: firstName,
                    //     lastName: lastName,
                    //     location: 'Santa Clara'
                    // };
                    // tabLinks.forEach(link => {
                    //     link.addEventListener('click', e => {
                    //         e.preventDefault();
                    //         const targetTab = e.target.getAttribute('data-tab');

                    //         // Remove active class from all links and content divs
                    //         tabLinks.forEach(link => link.classList.remove('active'));
                    //         tabContents.forEach(content => content.classList.remove('active'));

                    //         // Add active class to clicked link and corresponding content div
                    //         e.target.classList.add('active');
                    //         document.getElementById(targetTab).classList.add('active');

                    //         // Load content for the selected tab
                    //         loadTabContent(targetTab, userData);
                    //     });
                    // });
                    // loadTabContent('profile');

                    // createUserPage(username, firstName, lastName, email, profilePicUrl);
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


function createLoginCookie(username, firstName, lastName, email, profilePicUrl, location = "") {
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + 14);
    const cookieValue = `username=${username}|${firstName}|${lastName}|${email}|${profilePicUrl}|${location}; expires=${expirationDate.toUTCString()}; path=/`;
    document.cookie = cookieValue;
}

function attachSignin(element) {
    auth2.attachClickHandler(element, {},
        function (googleUser) {
            const profile = googleUser.getBasicProfile();
            const username = profile.getId();
            const firstName = profile.getGivenName();
            const lastName = profile.getFamilyName();
            const email = profile.getEmail();
            const profilePicUrl = profile.getImageUrl();
            createLoginCookie(username, firstName, lastName, email, profilePicUrl);
            document.getElementById("login-window").setAttribute("style", "display: none");
            showUserPage(username, firstName, lastName, email, profilePicUrl, location=null)
            // const userData = {
            //     profilePic: profilePicUrl,
            //     username: username,
            //     firstName: firstName,
            //     lastName: lastName,
            //     location: 'Santa Clara'
            // };
            // tabLinks.forEach(link => {
            //     link.addEventListener('click', e => {
            //         e.preventDefault();
            //         const targetTab = e.target.getAttribute('data-tab');

            //         // Remove active class from all links and content divs
            //         tabLinks.forEach(link => link.classList.remove('active'));
            //         tabContents.forEach(content => content.classList.remove('active'));

            //         // Add active class to clicked link and corresponding content div
            //         e.target.classList.add('active');
            //         document.getElementById(targetTab).classList.add('active');

            //         // Load content for the selected tab
            //         loadTabContent(targetTab, userData);
            //     });
            // });
            // loadTabContent('profile');
            // createUserPage(username, firstName, lastName, email, profilePicUrl);
            document.getElementById("userPage").setAttribute("style", "display: flex");
            addUser(backendUrl, firstName, lastName, email, username=email.split('@')[0], location=null, password=null, profilePic=profilePicUrl);
            // fetch(`${backendUrl}new_user/`, {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify({ firstName, lastName, email })
            // })
            // .then(response => {
            //     if (response.ok) {
            //         console.log('User Added');
            //     } else {
            //         console.log('Error adding user: ', response.status);
            //     }
            // })
            // .catch(error => {
            //     console.log('Error: ', error)
            // })
        });
}

function addUser(backendUrl, firstName, lastName, email, username, location=null, password = null, profilePic="https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png") {
    fetch(`${backendUrl}new_user/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ firstName, lastName, email, username, location, password, profilePic })
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

// function createUserPage(username, firstName, lastName, email, profilePicUrl) {
//     addUser(backendUrl, firstName, lastName, email);
//     const userPageElement = document.createElement('div');
//     userPageElement.classList.add('userPage');
//     userPageElement.id = 'userPage';
//     userPageElement.innerHTML = `
//       <div class="user-info">
//         <img src="${profilePicUrl}" id="pic" class="profile-pic" />
//         <div class="user-details">
//           <div class="title">
//             <p class="data-text"><strong>Name:</strong></p>
//             <p class="data-text value">${firstName} ${lastName}</p>
//           </div>
//           <div class="title">
//             <p class="data-text"><strong>Email:</strong></p>
//             <p class="data-text value">${email}</p>
//           </div>
//           <div class="title">
//             <p class="data-text"><strong>Current Plan:</strong></p>
//             <p class="data-text value" id="user-tier"></p>
//           </div>
//         </div>
//       </div>
//       <div class="userPage-button">
//         <button type="button" class="sign-out" onclick="signOut();">Sign Out</button>
//         <button type="button" class="subscribe" onclick="subscription();">Upgrade</button>
//       </div>
//       <div id="signout-modal" class="signout-modal">
//         <div class="signout-modal-content">
//           <p class="data-text">Are you sure you want to sign out?</p>
//           <button type="button" class="confirm-signout" onclick="confirmSignOut()">Yes</button>
//           <button type="button" class="cancel-signout" onclick="closeSignOutModal()">Cancel</button>
//         </div>
//       </div>
//     `;
//     document.body.appendChild(userPageElement);
// }

buttons.forEach(button => button.addEventListener('click', () => setActiveButton(button)));

const user_details = getCookie('username');
let { username = 'unknown', firstName, lastName, email, profilePicUrl = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png" } = user_details || {};
messageInput.addEventListener('keyup', () => {
    const message = messageInput.value.trim();
    if (message) {
        sendButton.addEventListener('click', (event) => {
            event.preventDefault();
            if (messageInput.value != '') {
                addUserMessage(messageInput.value, profilePicUrl);
                const messageVal = messageInput.value;
                addGeneratingMessage();
                fetch(`${backendUrl}get_response/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_message: messageVal,
                        user: username
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
            }
        });
        messageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                if (messageInput.value != '') {
                    addUserMessage(messageInput.value, profilePicUrl);
                    const messageVal = messageInput.value;
                    addGeneratingMessage();
                    fetch(`${backendUrl}get_response/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_message: messageVal,
                            user: username
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
                }
            }
        });
    }
});


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
    const contentDiv = document.getElementById(tab);

    // Clear existing content
    contentDiv.innerHTML = '';

    // Load content based on the selected tab
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

function updateUserData(firstName, lastName, username, location, profilePicUrl="https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png") {
    const email_id = getCookie('username').email
    fetch(`${backendUrl}update_user/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email_id, firstName, lastName, username, location, profilePicUrl })
    })
        .then(response => response.json())
        .then(data => {
            console.log('User Data Updated!');
            // Handle successful registration
        })
        .catch(error => console.error(error));

}

function loadProfileContent(contentDiv, userData) {
    // const userData = {
    //     profilePic: 'https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png',
    //     username: 'johndoe',
    //     firstName: 'John',
    //     lastName: 'Doe',
    //     location: 'New York'
    // };

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
            <label>Location: <input id="location" type="text" value="${userData.location}"></label>
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
    const email_id = getCookie('username').email
    const newUsername = profileForm.querySelector('#username');
    const newUsernameError = profileForm.querySelector('#usernameError')
    const firstNameInput = profileForm.querySelector('#firstname')
    const lastNameInput = profileForm.querySelector('#lastname')
    const locationInput = profileForm.querySelector('#location')
    let newProfilePic = "https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png"
    const profilePicInput = profileForm.querySelector('#profilePicInput');
    const profilePicCanvas = profileForm.querySelector("#profilePicCanvas");
    profilePicInput.addEventListener('change', () => {
        updateProfilePic(profilePicInput, profilePicCanvas);
        const file = profilePicInput.files[0];
        const formData = new FormData();
        formData.append('profilePic', file)
        formData.append('email_id', email_id)
        
        fetch(`${backendUrl}uploadProfilePic/`, {
            method: 'POST',
            body: formData
        })
        .then(response  => response.json())
        .then(data => {
            if (data.resp){
                newProfilePic = data.url
            }
            else {
                
                console.log('Error uploading the pic: ', data.error)
            }
        })
        .catch(error => {
            console.error('Error uploading the pic: ', error);
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

    saveChangesBtn.addEventListener('click', () => {
        updateUserData(firstNameInput.value, lastNameInput.value, newUsername.value, locationInput.value, newProfilePic)
        createLoginCookie(newUsername.value, firstNameInput.value, lastNameInput.value, email_id, newProfilePic, locationInput.value);
    })

    contentDiv.appendChild(profileForm);
}

function showPasswordForm() {
    const profileForm = document.querySelector('#profile form');
    // console.log(profileForm)
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
        // validatePassword(passwordInput.value, confirmPasswordInput.value, passwordError, createAccountButton);
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
            // Handle successful registration
        })
        .catch(error => console.error(error));

    // ... send newPassword to the backend

    const passwordForm = document.querySelector('.updPass');
    passwordForm.remove();

    const profileForm = document.querySelector('#profile form');
    profileForm.style.display = 'block';
}

function saveProfileChanges(e) {
    e.preventDefault();

    const firstName = document.querySelector('#profile form input[type="text"]').value;
    const lastName = document.querySelectorAll('#profile form input[type="text"]')[1].value;
    const location = document.querySelectorAll('#profile form input[type="text"]')[2].value;
    // ... send firstName, lastName, location to the backend

    const saveChangesBtn = document.querySelector('#saveChanges');
    saveChangesBtn.style.display = 'none';
}


function loadFilesContent(contentDiv) {
    // Fetch files data from the backend
    // const filesData = [
    //     { title: 'File 1', url: 'file1.html', thumbnail: 'file1.jpg' },
    //     { title: 'File 2', url: 'file2.html', thumbnail: 'file2.jpg' },
    //     // ... add more files
    // ];
    const filesData = []

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
        // Handle adding items from local storage
        fileInput.click();
        console.log('Adding items from local storage');
    });

    fileInput.addEventListener('change', async (event) => {
        const files = event.target.files;

        // Create a FormData object to send the files to the backend
        const formData = new FormData();

        // Append each file to the FormData object
        for (const file of files) {
            formData.append('files', file);
        }

        try {
            // Send the FormData object to the backend using fetch
            const response = await fetch(`${backendUrl}upload_forms/`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                console.log('Files uploaded successfully');
            } else {
                console.error('Error uploading files');
            }
        } catch (error) {
            console.error('Error uploading files:', error);
        }
    });
}

function loadLawyersContent(contentDiv) {
    // Fetch lawyers data from the backend
    const lawyersData = [
        { title: 'Lawyer 1', url: 'lawyer1.html', thumbnail: 'lawyer1.jpg' },
        { title: 'Lawyer 2', url: 'lawyer2.html', thumbnail: 'lawyer2.jpg' },
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
    // Fetch user email from the backend
    const userEmail = 'johndoe@example.com';

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

function loadFormsContent(contentDiv) {
    // Fetch forms data from the backend
    // const formsData = [
    //     { title: 'Form 1', url: 'form1.html', thumbnail: 'form1.jpg' },
    //     { title: 'Form 2', url: 'form2.html', thumbnail: 'form2.jpg' },
    //     // ... add more forms
    // ];
    const formsData = []
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
        formLink.classList.add('form-link');

        const formImage = document.createElement('div');
        formImage.classList.add('form-image');
        formImage.style.backgroundImage = `url('${form.imageUrl}')`;

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
        // Handle adding items from local storage
        fileInput.click();
        console.log('Adding items from local storage');
    });

    fileInput.addEventListener('change', async (event) => {
        const files = event.target.files;

        // Create a FormData object to send the files to the backend
        const formData = new FormData();

        // Append each file to the FormData object
        for (const file of files) {
            formData.append('files', file);
        }

        try {
            // Send the FormData object to the backend using fetch
            const response = await fetch(`${backendUrl}upload_forms/`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                console.log('Files uploaded successfully');
            } else {
                console.error('Error uploading files');
            }
        } catch (error) {
            console.error('Error uploading files:', error);
        }
    });
}