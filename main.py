from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler,filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re, time

MAIN, ADDING_TASK, REMOVE_TODO = range(3)

keyboard = [
    [InlineKeyboardButton("Add New Task \u2795\ufe0f", callback_data='add_todo')],
    [InlineKeyboardButton("Show All Tasks \U0001F5D2", callback_data='show_todo')],
    [InlineKeyboardButton("Show All Done Tasks \u2705", callback_data='show_done_todo')],
    [InlineKeyboardButton("Remove Task \u274c", callback_data='remove_todo')],
    [InlineKeyboardButton("Tasks that have expired \u23f0", callback_data='tasks_times_ended')],
    ]
reply_markup = InlineKeyboardMarkup(keyboard)


async def start(update, context):
    if 'TODOS_LIST' not in context.user_data:
        context.user_data['TODOS_LIST'] = []
    if 'DONE_TODOS_LIST' not in context.user_data:
        context.user_data['DONE_TODOS_LIST'] = []
    if 'TIME_ENDED_LIST' not in context.user_data:
        context.user_data['TIME_ENDED_LIST'] = []
    await update.effective_message.reply_text(f'''
    Hello {update.effective_user.first_name} \U0001F44B\U0001F3FC
Send me your Tasks \U0001F5D2 and I give you a list so you can handle them better.''', reply_markup=reply_markup)
    return MAIN



async def help(update, context):
    await update.effective_message.reply_text(f'''
Send me your Tasks \U0001F5D2 and I give you a list so you can handle them better.
''', reply_markup=reply_markup)
    return MAIN



async def menu(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    if query:
        await query.answer()
        await query.edit_message_text("Choose one of the following:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Choose one of the following:", reply_markup=reply_markup)
    return MAIN



async def alarm(context) -> None:
    todo_list = context.user_data['TODOS_LIST']
    time_over_list = context.user_data['TIME_ENDED_LIST']
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Beep \u203C Time for task  '{job.data}'  is over! \u23f0 \n")
    for job in context.job_queue.get_jobs_by_name(job.data):
        job.schedule_removal()
    timed_over_task = todo_list.remove(job.data)
    time_over_list.append(job.data)
    await context.bot.send_message(job.chat_id, text="Choose one of the following :", reply_markup=reply_markup)



async def regular_input(update, context):
    query = update.callback_query
    await query.edit_message_text(text='''Send me your tasks to add.
You can send me a list of tasks (one task per line!).
You can use these formats for sending tasks to me:\n
    your_task : only add a task
    your_task.(d,h,m).time : task with time
            (d = day , h = hour , m = minute) \n
Use /cancle to cancel the operation.''')
    return ADDING_TASK



async def add_todo(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_message.chat_id
    todo_list = context.user_data['TODOS_LIST']
    text = update.message.text
    text = text.split("\n")
    for item in text:
        if "." in item: # task with time sets with .h or .d
            item = item.split(".")
            if item[0] in todo_list:
                for job in context.job_queue.get_jobs_by_name(item[0]):
                    job.schedule_removal() # remove task times to set a new times for that
                if item[1] == "d":
                    context.job_queue.run_once(alarm, int(item[2]) * 86400, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                elif item[1] == "h":
                    context.job_queue.run_once(alarm, int(item[2]) * 3600, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                elif item[1] == "m":
                    context.job_queue.run_once(alarm, int(item[2]) * 60, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                else:
                    await update.effective_message.reply_text("The format you sent is incorrect \u274c")
                    return await menu(update, context)
                await update.effective_message.reply_text("The time has been successfully updated \u2705")

            elif item == '/cancle':
                return await menu(update, context)

            else:
                if item[1] == "d":
                    context.job_queue.run_once(alarm, int(item[2]) * 86400, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                elif item[1] == "h":
                    context.job_queue.run_once(alarm, int(item[2]) * 3600, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                elif item[1] == "m":
                    context.job_queue.run_once(alarm, int(item[2]) * 60, user_id=user_id, chat_id=chat_id, name=str(item[0]), data=item[0])
                else:
                    await update.effective_message.reply_text("The format you sent is incorrect \u274c")
                    return await menu(update, context)
                todo_list.append(item[0])
                await update.effective_message.reply_text(f"Task  '{item[0]}'  has been added with time  '{item[2]}'  success. \u2705")

        else:
            if item in todo_list:
                await update.effective_message.reply_text(f"The task  '{item}'  has already been in your TODOs. \u203C")

            elif item == '/cancle':
                return await menu(update, context)

            else:
                todo_list.append(item)
                await update.effective_message.reply_text(f"Task  '{item}'  added successfully. \u2705 ")
    await update.message.reply_text("Choose one of the following :", reply_markup=reply_markup)
    return MAIN



async def show_todo(update, context):
    keyboard = [
    [InlineKeyboardButton("Back \u21a9\ufe0f", callback_data='back')],
    ]
    reply_markup_2 = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    todo_list = context.user_data['TODOS_LIST']
    if not todo_list:
        await query.edit_message_text(text='You have no tasks. \u203c\ufe0f')
        time.sleep(1)
        return await menu(update, context)
    message = 'All of your tasks are : \n\n'
    message += '\n'.join([f'{i+1}. {todo}' for i, todo in enumerate(todo_list)])
    await query.edit_message_text(text=message, reply_markup=reply_markup_2)
    return MAIN



async def show_done_todo(update, context):
    keyboard = [
    [InlineKeyboardButton("Back \u21a9\ufe0f", callback_data='back')],
    ]
    reply_markup_2 = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    done_todo_list = context.user_data['DONE_TODOS_LIST']
    if not done_todo_list:
        await query.edit_message_text(text='You have no tasks. \u203c\ufe0f')
        time.sleep(1)
        return await menu(update, context)
    message = 'All the tasks you have done are : \n\n'
    message += '\n'.join([f'\u2714\ufe0f {todo}' for i, todo in enumerate(done_todo_list)])
    await query.edit_message_text(text=message, reply_markup=reply_markup_2)
    return MAIN



async def tasks_times_ended(update, context):
    keyboard = [
    [InlineKeyboardButton("Back \u21a9\ufe0f", callback_data='back')],
    ]
    reply_markup_2 = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    time_over_list = context.user_data['TIME_ENDED_LIST']
    if not time_over_list:
        await query.edit_message_text(text='You have no time ended tasks. \u203c\ufe0f')
        time.sleep(1)
        return await menu(update, context)
    message = 'All tasks that have expired are : \n\n'
    message += '\n'.join([f'\u2714\ufe0f {todo}' for i, todo in enumerate(time_over_list)])
    await query.edit_message_text(text=message, reply_markup=reply_markup_2)
    return MAIN



async def remove_todo_list(update, context):
    todo_list = context.user_data['TODOS_LIST']
    keyboard = []
    query = update.callback_query
    if len(todo_list) == 0:
        await query.edit_message_text(text='You have no tasks. \u203c\ufe0f')
        time.sleep(1)
        return await menu(update, context)
    else:
        for i, todo in enumerate(todo_list):
            keyboard.append([(InlineKeyboardButton(str(todo)+ '\u274c', callback_data=str(i)))])
    keyboard.append([(InlineKeyboardButton("Back \u21a9\ufe0f", callback_data='back'))])
    reply_markup_3 = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Select one to delete :", reply_markup=reply_markup_3)
    return REMOVE_TODO



async def removing_todo(update, context):
    todo_list = context.user_data['TODOS_LIST']
    done_todo_list = context.user_data['DONE_TODOS_LIST']
    query = update.callback_query
    data = query['data']
    done_task = todo_list.pop(int(data)) # remove task from todos list
    done_todo_list.append(done_task) # added task to done tasks list
    current_jobs = context.job_queue.get_jobs_by_name(done_task) # see if the task had time and if had remove it
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
    await query.answer()
    await query.edit_message_text(text="Task removed successfully. \u2705")
    time.sleep(1)
    return await remove_todo_list(update, context)



app = ApplicationBuilder().token("#your-token").build()
conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [
                CallbackQueryHandler(regular_input, pattern="^add_todo$"),
                CallbackQueryHandler(show_todo, pattern="^show_todo$"),
                CallbackQueryHandler(remove_todo_list, pattern="^remove_todo$"),
                CallbackQueryHandler(show_done_todo, pattern="^show_done_todo$"),
                CallbackQueryHandler(tasks_times_ended, pattern="^tasks_times_ended$"),
                CallbackQueryHandler(menu, pattern="^back$"),
            ],
            ADDING_TASK: [
                MessageHandler(filters.TEXT | filters.Regex("^/cancle$") ,add_todo),
            ],
            REMOVE_TODO: [
                CallbackQueryHandler(menu, pattern="^back$"),
                CallbackQueryHandler(removing_todo, pattern=re.compile(r'(^\d*)')),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^help$"), help)],
    )
app.add_handler(conv_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.run_polling()
