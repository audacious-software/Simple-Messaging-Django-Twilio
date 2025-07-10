define(['material', 'cards/node', 'jquery'], function (mdc, Node) {
  class SendMediaMessageNode extends Node {
    editBody () {
      let body = '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'

      body += `  <label class="mdc-text-field mdc-text-field--outlined" id="${this.cardId}_media_url_field" style="width: 100%">`
      body += '    <span class="mdc-notched-outline">'
      body += '      <span class="mdc-notched-outline__leading"></span>'
      body += '      <div class="mdc-notched-outline__notch">'
      body += `        <label for="${this.cardId}_media_url_value" class="mdc-floating-label">Media URL</label>`
      body += '      </div>'
      body += '      <span class="mdc-notched-outline__trailing"></span>'
      body += '    </span>'
      body += `    <input type="text" class="mdc-text-field__input" style="width: 100%" id="${this.cardId}_media_url_value" />`
      body += '  </label>'
      body += '</div>'
      
      body += '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
      body += `  <label class="mdc-text-field mdc-text-field--outlined mdc-text-field--textarea" id="${this.cardId}_message_field" style="width: 100%">`
      body += '    <span class="mdc-notched-outline">'
      body += '      <span class="mdc-notched-outline__leading"></span>'
      body += '      <div class="mdc-notched-outline__notch">'
      body += `        <label for="${this.cardId}_message_value" class="mdc-floating-label">Message</label>`
      body += '      </div>'
      body += '      <span class="mdc-notched-outline__trailing"></span>'
      body += '    </span>'
      body += '    <span class="mdc-text-field__resizer">'
      body += `      <textarea class="mdc-text-field__input" rows="4" style="width: 100%" id="${this.cardId}_message_value"></textarea>`
      body += '    </span>'
      body += '  </label>'
      body += '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-7 mdc-typography--caption" style="padding-top: 8px;">'
      body += '  The message above will be sent to the user and the system will proceed to the next card.'
      body += '</div>'
      body += '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-5" style="padding-top: 8px; text-align: right;">'
      body += `  <button class="mdc-icon-button" id="${this.cardId}_next_edit">`
      body += '    <i class="material-icons mdc-icon-button__icon" aria-hidden="true">create</i>'
      body += '  </button>'
      body += `  <button class="mdc-icon-button" id="${this.cardId}_next_goto">`
      body += '    <i class="material-icons mdc-icon-button__icon" aria-hidden="true">navigate_next</i>'
      body += '  </button>'
      body += '</div>'
      body += `<div class="mdc-dialog" role="alertdialog" aria-modal="true" id="${this.cardId}-edit-dialog"  aria-labelledby="${this.cardId}-dialog-title" aria-describedby="${this.cardId}-dialog-content">`
      body += '  <div class="mdc-dialog__container">'
      body += '    <div class="mdc-dialog__surface">'
      body += `      <h2 class="mdc-dialog__title" id="${this.cardId}-dialog-title">Choose Destination</h2>`
      body += `      <div class="mdc-dialog__content" id="${this.cardId}-dialog-content"  style="padding: 0px;">`

      body += this.dialog.chooseDestinationMenu(this.cardId)
      body += '      </div>'
      body += '    </div>'
      body += '  </div>'
      body += '  <div class="mdc-dialog__scrim"></div>'
      body += '</div>'

      return body
    }

    viewBody () {
      let body = '<div class="mdc-typography--body1" style="margin: 16px;">'
      body += `<img src="${this.definition.media_url}" style="width: 100%; border: thin solid; black;" />`
      body += `<div>Sends: <em>${this.definition.message}</em></div>`
      body += '</div>'
      
      return body
    }

    updateCharacterCount () {
      const value = $(`#${this.cardId}_message_value`).val()

      const msgLength = value.length

      if (msgLength === 1) {
        $(`[for="${this.cardId}_message_value"]`).html('Message (1 character)')
      } else {
        $(`[for="${this.cardId}_message_value"]`).html(`Message (${msgLength} characters)`)
      }
    }

    initialize () {
      super.initialize()

      const me = this

      const messageField = mdc.textField.MDCTextField.attachTo(document.getElementById(`${this.cardId}_message_field`))
      messageField.value = this.definition.message

      $(`#${this.cardId}_message_value`).on('change keyup paste', function () {
        const value = $('#' + me.cardId + '_message_value').val()

        me.definition.message = value

        me.updateCharacterCount()

        me.dialog.markChanged(me.id)
      })

      me.dialog.initializeDestinationMenu(me.cardId, function (selected) {
        me.definition.next_id = selected

        me.dialog.markChanged(me.id)
        me.dialog.loadNode(me.definition)
      })

      const mediaUrlField = mdc.textField.MDCTextField.attachTo(document.getElementById(`${this.cardId}_media_url_field`))
      mediaUrlField.value = this.definition.media_url

      $(`#${this.cardId}_message_value`).on('change keyup paste', function () {
        const value = $('#' + me.cardId + '_media_url_value').val()

        me.definition.media_url = value

        me.dialog.markChanged(me.id)
      })

      me.dialog.initializeDestinationMenu(me.cardId, function (selected) {
        me.definition.next_id = selected

        me.dialog.markChanged(me.id)
        me.dialog.loadNode(me.definition)
      })

      const dialog = mdc.dialog.MDCDialog.attachTo(document.getElementById(me.cardId + '-edit-dialog'))

      $(`#${this.cardId}_next_edit`).on('click', function () {
        dialog.open()
      })

      $(`#${this.cardId}_next_goto`).on('click', function () {
        const destinationNodes = me.destinationNodes(me.dialog)

        for (let i = 0; i < destinationNodes.length; i++) {
          const destinationNode = destinationNodes[i]

          if (me.definition.next_id === destinationNode.id) {
            $(`[data-node-id="${destinationNode.id} "]`).css('background-color', '#ffffff')
          } else {
            $(`[data-node-id="${destinationNode.id} "]`).css('background-color', '#e0e0e0')
          }
        }

        const sourceNodes = me.sourceNodes(me.dialog)

        for (let i = 0; i < sourceNodes.length; i++) {
          const sourceNode = sourceNodes[i]

          if (me.definition.next_id === sourceNode.id) {
            $(`[data-node-id="${sourceNode.id} "]`).css('background-color', '#ffffff')
          } else {
            $(`[data-node-id="${sourceNode.id} "]`).css('background-color', '#e0e0e0')
          }
        }
      })

      me.updateCharacterCount()
    }

    destinationNodes (dialog) {
      const nodes = super.destinationNodes(dialog)

      const id = this.definition.next_id

      for (let i = 0; i < this.dialog.definition.length; i++) {
        const item = this.dialog.definition[i]

        if (item.id === id) {
          nodes.push(Node.createCard(item, dialog))
        }
      }

      if (nodes.length === 0) {
        const node = this.dialog.resolveNode(id)

        if (node !== null) {
          nodes.push(node)
        }
      }

      return nodes
    }

    updateReferences (oldId, newId) {
      if (this.definition.next_id === oldId) {
        this.definition.next_id = newId
      }
    }

    issues () {
      const issues = super.issues()

      if (this.definition.next_id === undefined) {
        issues.push([this.definition.id, 'Next node does not point to another node.', this.definition.name])
      } else if (this.definition.next_id === this.definition.id) {
        issues.push([this.definition.id, 'Next node points to self.', this.definition.name])
      } else if (this.definition.media_url === undefined || this.definition.media_url === null || this.definition.media_url === '') {
        issues.push([this.definition.id, 'Media URL field is empty.', this.definition.name])
      }

      if (this.isValidDestination(this.definition.next_id) === false) {
        issues.push([this.definition.id, 'Next node points to a non-existent node.', this.definition.name])
      }

      return issues
    }

    cardType () {
      return 'Twilio: Send Media Message'
    }

    static cardName () {
      return 'Twilio: Send Media Message'
    }

    static createCard (cardName) {
      const card = {
        name: cardName,
        context: '(Context goes here...)',
        message: '(Message goes here...)',
        media_url: 'https://placehold.co/600x400',
        type: 'send-media-message',
        id: Node.uuidv4(),
        next_id: null
      }

      return card
    }
  }

  Node.registerCard('send-media-message', SendMediaMessageNode)

  return SendMediaMessageNode
})
