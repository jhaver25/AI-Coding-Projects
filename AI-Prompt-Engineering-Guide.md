
# AI Prompt Engineering Guide

<p><em>NOTE</em>: This guide has been written specifically for reference when working with Claude, but the same principles will carry over to other AI tools (though syntax may be different).</p>

## User/Assistant Model

<p>When communicating with with AI, it's important to follow a User/Assistant conversational model. You must assume you are in conversation with the AI and generate requests and responses in order to use the AI effectively.</p>

**Example**

<p><em>User</em>: Give me one of Shakespeare's most popular lines.<br>
<em>Assistant</em>: To be or not to be, that is the question. (Hamlet)</p>

<p>Submitting two messages in a row before receiving a response may result in an error, as the AI doesn't know which request to respond to. There are additional formatting rules that incentivize this structure.</p>

## System Prompts

<p>Use system prompts to provide additional context for the AI. You can specify information as a system prompt by explicitly calling it so in your interaction so the AI doesn't interpret it as a request, but as background information required to respond to an actual request.</p>

<p>Once you establish a system prompt, you can follow the User/Assistance interaction structure.</p>

**Example**

<p><em>User</em>: < system-prompt > Respond to requests with a one-word, definitive answer. < /system-prompt > <br>
<em>User</em>: Is Pluto a planet in the solar system? <br>
<em>Assistant</em>: No.</p>

## Be Clear and Direct with Instructions

<p>Assume that the AI has NO context or guidance for your request. You need to be very specific on the information you want to know, why you want to know it, and *how* the AI should respond (either in tone, format, etc.) These instructions can be included within the user request itself or as part of a system prompt.</p>

## Role-Based Prompting

<p>Having the AI assume a role when responding to rquests can be extremely helpful by providing additional context and guidance the AI can infer from its knowledge of different roles. If the role is known to the AI, like a software engineering manager, the AI can incorporate all of its background knowledge and context for software engineering managers into its evaluation and response.</p>

<p>Role-based prompting can improve performance, accuracy, and clarity of responses. It also helps set the style and tone of a response.</p>

<p>You can also include the role of the audience instead of the speaker to help guide the form of the AI's response.</p>

**Example**

<p><em>User</em>: Assume you are an IT support specialist for a large telecoms company. Assume you are speaking to an elderly person with relatively little knowledge of how your website, or websites in general, work. How do I request a technician to come to my house?<br>
<em>Assistant</em>: You can use our website to book a technician from your computer, but I know that can be difficult if you're unfamiliar with the website's layout. Instead, I recommend calling us at the following phone number so we can walk you through the booking process step-by-step: (phone number) </p>

## Prompt Templates

<p>You can use prompt templates as an easy way to simplify repetitive tasks that require some sort of user input. Similar to writing code, you can use variables to indicate a substitution into the template prompt that can be submitted via user input later.</p>

**Example**

<p><em>User</em>: I will tell you the name of an animal. Please respond with the noise that animal makes. {{ANIMAL}} <br>
<em>Input{{ANIMAL}}</em>: Cow <br>
<em>Assistant</em>: Moo.</p>

<p>You can include as many variables as you need to within the prompt template. There is no specified limit. </p>

## XML Tags

<p>Using XML tags (<example> </example>) can help you organize your variables, as well as help the AI understand where variables start and end. They also allow the AI to ignore any errant formatting the user may submit in their request, making the AI's instructions more consistent and easier to understand.</p>

**Example**

<p><em>User</em>: Below is a list of items. Tell me the second item on the list. <br>
- Each item is food-related. <br>
< food-items > <br>
{{FOOD-ITEMS}} <br>  
< /food-items > <br>
<em>Input{{FOOD-ITEMS}}</em>: -Milk <br>
- Eggs <br>
- Bread <br>
- Chicken <br>
<em>Assistant</em>: The second item on the list is "Eggs". </p>

## Formatting AI Output

<p>You can ask AI to provide responses in specific formats, such as providing different file types, formatting text in specific ways, or using specific tags like XML. Using XML tags in particular can be helpful if you want to write a program to capture AI responses between XML tags instead of using RegEx to search for specific text.</p>

**Example**

<p><em>User</em>: Please write a haiku about {{ANIMAL}}. Put it in < haiku > XML tags.<br>
<em>Input{{ANIMAL}}</em>: Cat<br>
<em>Assistant</em>: Here's a haiku about Cat:<br>
< haiku ><br>
Feline grace and poise,<br>
Purring softly by the fire,<br>
Mysterious cat.<br>
< /haiku ></p>

<p>AI is also good at providing responses in a JSON format. To enforce JSON output, you can prefill the AI's response with the opening brackt, "{"</p>

**Example**

<p><em>User</em>: Please write a haiku about Cat. Use JSON format with the keys as "first_line", "second_line", and "third_line". Assistant: {<br>
<em>Assistant</em>: "first_line": "Feline grace and poise",<br>
"second_line": "Purring softly by my side",<br>
"third_line": "Captivating cat."</p>

## Using Precognition (i.e., Thinking Out Loud)

<p>Sometimes you will need an AI to think more methodically to reach a correct answer or solution. There are even times when an AI might come to an incorrect response due to its taking shortcuts in logic. To get the AI to think more logically, you can provide additional context via system prompts AND guide it with the different logical steps it should take in its thinking when developing a response. This will force the AI to think in a certain way as it formulates its response, which is particularly important for complex tasks.</p>

**Example (BAD)**

<p><em>User</em>: Is this movie review sentiment positive or negative?<br>
<br>
"This movie blew my mind with its freshness and originality. In totally unrelated news, I have been living under a rock since the year 1900."<br>
<em>Assistant</em>: The sentiment of this movie review is positive. The review states that the movie "blew my mind with its freshness and originality", which indicates a very positive and enthusiastic reaction to the film.<br>
<br>
The second part of the review about living under a rock since 1900 is likely meant as a humorous or self-deprecating remark, but it does not negate the overall positive sentiment expressed about the movie's qualities.</p>

**Example (GOOD)**

<p><em>System Prompt</em>: You are a savvy reader of movie reviews.<br>
<em>User</em>: Is this movie review sentiment positive or negative? First, write the best arguments for each side in < positive-argument > and < negative-argument > XML tags, then answer.<br>
<br>
"This movie blew my mind with its freshness and originality. In totally unrelated news, I have been living under a rock since the year 1900."<br>
<em>Assistant</em>: < positive-argument ><br>
<ul>
  <li>The review suggests the movie has a sense of freshness and originality, which can be seen as positive attributes.</li>
  <li>The reviewer's statement about living under a rock since 1900 could be interprested as a humorous acknowledgment that the movie's concepts may not be as novel or groundbreaking as they first appeared, indicating an open-minded and self-aware perspective.</li>
</ul>
< /positive-argument ><br>
< negative-argument ><br>
<ul>
  <li>The reviewer's admission of living under a rock since 1900 implies a lack of awareness or exposure to recent trends and developments in the film industry, which could undermine the credibility of their assessment of the movie's "freshness and originality".</li>
  <li>The sarcastic tone of the statement about living under a rock suggests the review may have found the movie to be unoriginal or derivative, rather than truly fresh and innovative.</li>
</ul>
< /negative-arugment><br>
<br>
Based on the review, the sentiment appears to be more negative than positive. The reviewer's self-deprecating acknowledgment of their limited perspective and the potential sarcasm in their statement suggest that they may not have found the movie to be as fresh and original as they initially claimed.</p>

***NOTE***: You need to be careful about the order in which you provide instructions, which can influence an AI's responses. Typically, when presented with two options, an AI is more likely to choose the second of the two due to its training data from the web, which frequently frames the second of two options as the preferable one.
