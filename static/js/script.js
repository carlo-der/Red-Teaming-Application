

async function runCrawler() {
    const button = document.getElementById('crawler'); // run crawler button
    const status = document.getElementById('status'); // crawler status is shown
    const result = document.getElementById('text-results'); //this is where the scraped results are stored


    button.disabled = true;
    button.textContent = 'Crawl in progress. This may take 3-5 minutes'; // this disables the button after it is clicked to ensure that only 1 crawl can be run at a time
    status.className= 'loading';
    status.textContent = 'Crawler is running. Please wait';
    result.innerHTML = '';

    

    try {
        const response = await fetch('/run-crawler', {
            method: 'POST'
            
        });
        

        const data = await response.json();

        if (data.status === 'success') {
            status.className='success';
            status.textContent = data.message;

            if(!data.data || data.data.length === 0) {
                status.className = 'error';
                status.textContent = 'No Data found';
                return;
            }

            localStorage.setItem('crawleroutput', JSON.stringify(data.data)); // saves the data locally for each session to allow users to see the crawled info if they reload the page
            localStorage.setItem('crawlerTime', new Date().toISOString());
            displayCrawlerFindings(data.data);

            
        }
        else {
            status.className = 'error';
            status.textContent = 'Error: ' + data.message; 
        }
    } catch (error) {
        status.className = 'error';
        status.textContent= 'Error: ' + error.message;

    }
    finally {
        button.disabled = false;
        button.textContent = 'Run Crawler'; // enables to button to be clicked again after the crawl has been run 
    }
}

async function generateEmails() {
    const button = document.getElementById('generatebutton');
    const emailstatus = document.getElementById('emailstatus');
    const emailResults = document.getElementById('emailResults');
    const template = document.getElementById('template');

    button.disabled=true;
    button.textContent= ' Generating Email ... (this can take 2-3 minutes)';
    emailstatus.className = 'loading';
    emailstatus.textContent = 'Generating Personalised Emails Using Ollama';
    emailResults.innerHTML='';

    try {
        const response = await fetch('/email-generator', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                template_type: template.value
            })

        });

        const data = await response.json();

        if(data.status =='success') {
            emailstatus.className ='success';
            emailstatus.textContent=` Generated ${data.count} emails`;
            localStorage.setItem('generatedemails', JSON.stringify(data.emails));
            localStorage.setItem('time', new Date(). toISOString());

            displayEmails(data.emails);
        }
        else {
            emailstatus.className= 'error';
            emailstatus.textContent='Error:' +data.message;
        }
    } 
    catch (error) {
        emailstatus.className ='error';
        emailstatus.textContent='Error:' +error.message;
    }
    finally {
        button.disabled=false;
        button.textContent= 'Generate Emails';
    }

}

function displayEmails(emails) {
    const result = document.getElementById('emailResults');
    let html = '';

    emails.forEach((email, index) => {
        html += `
            <div class="email-card">
                <div class="email-header">
                    <h3> Email ${index +1}: ${email.name || 'Unknown'}</h3>
                    <button onclick="sendEmail(${index})" class="btn-small">Send to inbox</button>
                </div>
                <div class="email-metadata">
                    <p class="para"><strong> To:</strong> sandbox-${index +1}@test.local</p>
                    <p class="para"><strong>From:</strong> ${email.sender} &lt;${email.name}&gt;</p>
                    <p class="para"><strong> Subject:</strong> ${email.subject}</p>
                </div>
                <div class="email-body">
                    <pre>${email.body}</pre>
                </div>
            </div>
        `;
    });
    result.innerHTML = html;
}

async function sendEmail(index){
    const sandboxedEmail = `sandox-${index+1}@test.local`;

    try {
        const response= await fetch('/send_email', {
            method:'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                recipient: sandboxedEmail,
                emailIndex: index
            })
        });

        const data =await response.json();

        if(data.status ==='success') {
            alert(`email ${index+1} sent to ${sandboxedEmail}`);
        }
        else{
            alert('Error: ' +data.message);
        }
        
    } 
    catch(error)
    {
        alert('Error sending email: ' +error.message);
    }


}


function displayCrawlerFindings(data){
    let resultContainer = document.getElementById('text-results'); //creation of a container to store data once scraped

    if(!resultContainer)
        {
            const parent =document.getElementById('result');
            if (parent)
                {
                    resultContainer= document.createElement('div');
                    resultContainer.id = 'text-results';
                    parent.appendChild(resultContainer);
                }
                else{
                    console.error("nothing found"); // error return if no information has beens scraped
                    return;
                }

        }

    resultContainer.innerHTML='';

    data.forEach(item => {

        

        const card = document.createElement('div');
        card.classList.add('crawler');

        if (item.type === 'course_summary') {
            card.classList.add('type_course');
            card.innerHTML =`
            <h2 class="course-scanned">Course Scanned</h2>
            <p class="para"><strong>URL:</strong> <a href="${item.url}" target="_blank">${item.url}</a></p>
            <p class="para"><strong>Names:</strong> ${item.extracted_staff.map(s => s.name).join(', ')}</p>
            
            
            `;


        }
        else if (item.type === 'staff_profile')
            {
                card.classList.add('type_staff');
                const name = item.name||'Name not found';
                const jobTitle = item.job_title || item.job_name || 'N/A';
                const email = (item.email && !item.email.includes('encrypted')) ? item.email : 'Not available';
                const interests = item.research_interests && item.research_interests.length >0 ? item.research_interests.filter(i => i).map(interest => `<li>${interest}</li>`).join('') : '<li>None Listed</li>';
                const qualifList = item.qualifications && item.qualifications.length >0 ? item.qualifications.filter(q => q).map(q => `<li>${q}</li>`).join(''): `<li>None Listed</li>`;
                const externalLinks= item.external_links && Object.keys(item.external_links).length>0 ? Object.entries(item.external_links).map(([platform, url]) => `<a href="${url}" target="_blank">${platform}</a>`).join(' | '): 'No External Links Found';
                
                // html formatting of the results
                card.innerHTML =` 
                <h3>${name}</h3>
                <p class="para"><strong>Job Title:</strong> ${jobTitle}</p>
                <p class="para"><strong>Email:</strong>${email}</p>
                <p class="para"><strong>Profile URL:</strong>${item.url}</p>
                <p class="para"><strong>Research Interests</strong></p>
                <ul>${interests}</ul>
                <p class="para"><strong>Qualifications</strong></p>
                <ul>${qualifList}</ul>
                <p class="para"><strong>External Links:</strong></p>
                <div>${externalLinks}</div>

                
                `;


                
                
            }

            resultContainer.appendChild(card);

            
        
    });
}

document.addEventListener('DOMContentLoaded', function(){

    if(!document.getElementById('crawler')) return;

    const savedScrape = localStorage.getItem('crawleroutput');
    const time = localStorage.getItem('crawlerTime');

    if (savedScrape) {
        const data = JSON.parse(savedScrape);
        const status = document.getElementById('status');
        if (time) {
            const date = new Date(time);
            status.className='success';
            status.textContent=`Crawler results from ${date.toLocaleString()}`;
        }

        displayCrawlerFindings(data);
    }
})

document.addEventListener('DOMContentLoaded', function(){

    if(!document.getElementById('generatebutton')) return;

    const savedemails = localStorage.getItem('generatedemails');
    const time = localStorage.getItem('time');

    if (savedemails) {
        const emails = JSON.parse(savedemails);
        const status = document.getElementById('emailstatus');
        if (time) {
            const date = new Date(time);
            status.className='success';
            status.textContent=`${emails.length} emails generated on ${date.toLocaleString()}`;
        }

        displayEmails(emails);
    }
})