
# AI Prompt Engineering Guide

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
