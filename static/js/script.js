

async function runCrawler() {
    const button = document.getElementById('crawler');
    const status = document.getElementById('status');
    const result = document.getElementById('text-results');


    button.disabled = true;
    button.textContent = 'Crawl in progress. This may take 3-5 minutes';
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
            //result.textContent= JSON.stringify(data.data, null, 2);
            //const resultContainer = document.getElementById('text-results');
            let resultContainer = document.getElementById('text-results');

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
                            console.error("nothing found");
                            return;
                        }

                }

            resultContainer.innerHTML='';

            data.data.forEach(item => {

                

                const card = document.createElement('div');
                card.classList.add('crawler');

                if (item.type === 'course_summary') {
                    card.classList.add('type_course');
                    card.innerHTML =`
                    <h2>Course Scanned</h2>
                    <p><strong>URL:</strong> <a href="${item.url}" target="_blank">${item.url}</a></p>
                    <p><strong>Names:</strong> ${item.extracted_staff.map(s => s.name).join(', ')}</p>
                    
                    
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

                        card.innerHTML =`
                        <h3>${name}</h3>
                        <p><strong>Job Title:</strong> ${jobTitle}</p>
                        <p><strong>Email:</strong>${email}</p>
                        <p><strong>Profile URL:</strong>${item.url}</p>
                        <p><strong>Research Interests</strong></p>
                        <ul>${interests}</ul>
                        <p><strong>Qualifications</strong></p>
                        <ul>${qualifList}</ul>
                        <p><strong>External Links:</strong></p>
                        <div>${externalLinks}</div>

                        
                        `;


                        //let external_url = 'None Found';
                        //if (item.external_links && Object.keys(item.external_links).length>0) {
                           // external_url = Object.entries(item.external_links)
                           // .map(([platform, url]) => `<a href="${url}" target="_blank" class="social-tag">${platform.toUpperCase()}</a>`)
                            //.join('');
                        //}

                        //card.innerHTML = `
                        //<h3 style="margin-top:0;"> ${item.name || 'Staff Member'}</h3>
                        //<p><strong>Role:</strong>${item.job_name || 'N/A'}</p>
                        //<p><strong>Email:</strong> <code>${item.email || 'Hidden'}</code></p>
                        //<p><strong>Research Interests:</strong> ${item.research_interests ? item.research_interests.join(', '): 'N/A'}</p>
                        //<p><strong>External Links:</strong> <div style="margin-top: 10px;">${external_url}</div></p>

                        //`;
                        
                    }

                    resultContainer.appendChild(card);

                    
                
            });

            
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
        button.textContent = 'Run Crawler';
    }
}