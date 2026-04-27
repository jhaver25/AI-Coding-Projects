
# AI Prompt Engineering Guide

## User/Assistant Model

<p>When communicating with with AI, it's important to follow a User/Assistant conversational model. You must assume you are in conversation with the AI and generate requests and responses in order to use the AI effectively.</p>

**Example**

<p>*User*: Give me one of Shakespeare's most popular lines.<br>
*Assistant*: To be or not to be, that is the question. (Hamlet)</p>

<p>Submitting two messages in a row before receiving a response may result in an error, as the AI doesn't know which request to respond to. There are additional formatting rules that incentivize this structure.</p>

## System Prompts

<p>Use system prompts to provide additional context for the AI. You can specify information as a system prompt by explicitly calling it so in your interaction so the AI doesn't interpret it as a request, but as background information required to respond to an actual request.</p>

<p>Once you establish a system prompt, you can follow the User/Assistance interaction structure.</p>

**Example**

<p>*User*: <system prompt> Respond to requests with a one-word, definitive answer. </system prompt>
*User*: Is Pluto a planet in the solar system?
*Assistant*: No.</p>

## Be Clear and Direct with Instructions

<p>Assume that the AI has NO context or guidance for your request. You need to be very specific on the information you want to know, why you want to know it, and *how* the AI should respond (either in tone, format, etc.) These instructions can be included within the user request itself or as part of a system prompt.</p>

## Role-Based Prompting

<p>Having the AI assume a role when responding to rquests can be extremely helpful by providing additional context and guidance the AI can infer from its knowledge of different roles. If the role is known to the AI, like a software engineering manager, the AI can incorporate all of its background knowledge and context for software engineering managers into its evaluation and response.</p>

<p>Role-based prompting can improve performance, accuracy, and clarity of responses. It also helps set the style and tone of a response.</p>

<p>You can also include the role of the audience instead of the speaker to help guide the form of the AI's response.</p>

**Example**

<p>*User*: Assume you are an IT support specialist for a large telecoms company. Assume you are speaking to an elderly person with relatively little knowledge of how your website, or websites in general, work. How do I request a technician to come to my house?
*Assistant*: You can use our website to book a technician from your computer, but I know that can be difficult if you're unfamiliar with the website's layout. Instead, I recommend calling us at the following phone number so we can walk you through the booking process step-by-step: (phone number) </p>
